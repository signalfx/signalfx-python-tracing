# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import types

from opentracing.mocktracer import MockTracer
from mock import Mock, MagicMock
import pymysql.connections
import pymysql.cursors
import opentracing
import pymysql
import mock

from signalfx_tracing.libraries.pymysql_.instrument import config, instrument, uninstrument
from .conftest import PyMySQLTestSuite


class MockDBAPICursor(Mock):

    execute = MagicMock(spec=types.MethodType)
    execute.__name__ = 'execute'

    executemany = MagicMock(spec=types.MethodType)
    executemany.__name__ = 'executemany'

    callproc = MagicMock(spec=types.MethodType)
    callproc.__name__ = 'callproc'

    rowcount = 'SomeRowCount'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self


class MockDBAPIConnection(Mock):

    commit = MagicMock(spec=types.MethodType)
    commit.__name__ = 'commit'

    rollback = MagicMock(spec=types.MethodType)
    rollback.__name__ = 'rollback'

    def cursor(self):
        return MockDBAPICursor()

    def __exit__(self, exc, value, tb):
        if exc:
            return self.rollback()
        return self.commit()


class TestPyMySQL(PyMySQLTestSuite):

    def test_noninstrumented_connection_does_not_trace(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                connection = pymysql.connect()
                with connection.cursor() as cursor:
                    cursor.execute('traced')
                    cursor.executemany('traced')
                    cursor.callproc('traced')

        assert not tracer.finished_spans()

    def test_uninstrumented_connections_no_longer_traces(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                instrument(tracer)
                connection = pymysql.connect()
                with connection.cursor() as cursor:
                    cursor.execute('traced')
                    cursor.executemany('traced')
                    cursor.callproc('traced')

                spans = tracer.finished_spans()
                assert len(spans) == 3
                assert spans[0].operation_name == 'MockDBAPICursor.execute(traced)'
                assert spans[1].operation_name == 'MockDBAPICursor.executemany(traced)'
                assert spans[2].operation_name == 'MockDBAPICursor.callproc(traced)'

                uninstrument()
                tracer.reset()

                connection = pymysql.connect()
                with connection.cursor() as cursor:
                    cursor.execute('traced')
                    cursor.executemany('traced')
                    cursor.callproc('traced')

                assert not tracer.finished_spans()


class TestPyMySQLConfig(PyMySQLTestSuite):

    def test_global_tracer_used_by_default(self):
        tracer = MockTracer()
        opentracing.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                instrument()
                connection = pymysql.connect()
                with connection.cursor() as cursor:
                    cursor.execute('traced')
                    cursor.executemany('traced')
                    cursor.callproc('traced')

        spans = tracer.finished_spans()
        assert len(spans) == 3
        assert spans[0].operation_name == 'MockDBAPICursor.execute(traced)'
        assert spans[1].operation_name == 'MockDBAPICursor.executemany(traced)'
        assert spans[2].operation_name == 'MockDBAPICursor.callproc(traced)'

    def test_cursor_commands_are_traced_by_default(self):
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                instrument()
                connection = pymysql.connect()
                with connection.cursor() as cursor:
                    cursor.execute('traced')
                    cursor.executemany('traced')
                    cursor.callproc('traced')

        spans = tracer.finished_spans()
        assert len(spans) == 3
        assert spans[0].operation_name == 'MockDBAPICursor.execute(traced)'
        assert spans[1].operation_name == 'MockDBAPICursor.executemany(traced)'
        assert spans[2].operation_name == 'MockDBAPICursor.callproc(traced)'

    def test_undesired_cursor_commands_are_not_traced(self):
        config.traced_commands = ['execute']
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                instrument()
                connection = pymysql.connect()
                with connection.cursor() as cursor:
                    cursor.executemany('untraced')
                    cursor.callproc('untraced')
                    cursor.execute('traced')

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'MockDBAPICursor.execute(traced)'

    def test_connection_commands_are_traced_by_default(self):
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                with mock.patch.object(pymysql.cursors.Cursor, 'callproc',
                                       side_effect=Exception) as callproc:
                    callproc.__name__ = 'callproc'

                    instrument()
                    connection = pymysql.connect()
                    with connection as cursor:
                        cursor.execute('traced')

                    spans = tracer.finished_spans()
                    assert len(spans) == 2
                    assert spans[0].operation_name == 'MockDBAPICursor.execute(traced)'
                    assert spans[1].operation_name == 'MockDBAPIConnection.commit()'

                    tracer.reset()
                    with connection as cursor:
                        cursor.callproc('traced')

                    spans = tracer.finished_spans()
                    assert len(spans) == 2
                    assert spans[0].operation_name == 'MockDBAPICursor.callproc(traced)'
                    assert spans[1].operation_name == 'MockDBAPIConnection.rollback()'

    def test_undesired_connection_commands_are_not_traced(self):
        config.traced_commands = ['rollback']
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                with mock.patch.object(pymysql.cursors.Cursor, 'callproc',
                                       side_effect=Exception) as callproc:
                    callproc.__name__ = 'callproc'

                    instrument()
                    connection = pymysql.connect()
                    with connection as cursor:
                        cursor.executemany('untraced')
                        cursor.execute('traced')

                    assert not tracer.finished_spans()

                    with connection as cursor:
                        cursor.callproc('untraced')

                    spans = tracer.finished_spans()
                    assert len(spans) == 1
                    assert spans[0].operation_name == 'MockDBAPIConnection.rollback()'

    def test_span_tags_are_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.span_tags = dict(custom='tag')

        with mock.patch.object(pymysql.connections, 'Connection', MockDBAPIConnection):
            with mock.patch.object(pymysql.cursors, 'Cursor', MockDBAPICursor):
                instrument()
                connection = pymysql.connect()
                with connection as cursor:
                    cursor.executemany('traced')
                    cursor.execute('traced')

                spans = tracer.finished_spans()
                assert len(spans) == 3
                assert spans[0].operation_name == 'MockDBAPICursor.executemany(traced)'
                assert spans[1].operation_name == 'MockDBAPICursor.execute(traced)'
                assert spans[2].operation_name == 'MockDBAPIConnection.commit()'
                for span in spans:
                    assert span.tags['custom'] == 'tag'
