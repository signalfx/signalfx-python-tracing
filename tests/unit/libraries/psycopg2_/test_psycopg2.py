# Copyright (C) 2019 SignalFx. All rights reserved.
import types

from opentracing.mocktracer import MockTracer
from opentracing.ext import tags
from mock import MagicMock
import psycopg2.extensions
import opentracing
import psycopg2
import mock

from signalfx_tracing.libraries.psycopg2_.instrument import (
    config,
    instrument,
    uninstrument,
)
from .conftest import Psycopg2TestSuite


class MockDBAPICursor(object):

    execute = MagicMock(spec=types.MethodType)
    execute.__name__ = "execute"

    executemany = MagicMock(spec=types.MethodType)
    executemany.__name__ = "executemany"

    callproc = MagicMock(spec=types.MethodType)
    callproc.__name__ = "callproc"

    rowcount = "SomeRowCount"

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self


class MockDBAPIConnection(object):

    commit = MagicMock(spec=types.MethodType)
    commit.__name__ = "commit"

    rollback = MagicMock(spec=types.MethodType)
    rollback.__name__ = "rollback"

    def __init__(self, *args, **kwargs):
        pass

    def cursor(self):
        return MockDBAPICursor()

    def get_dsn_parameters(self):
        return dict(dbname="test")

    def __exit__(self, exc, value, tb):
        if exc:
            return self.rollback()
        return self.commit()


class TestPsycopg2(Psycopg2TestSuite):
    def test_noninstrumented_connection_does_not_trace(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
            connection = psycopg2.connect(
                "dbname=test", connection_factory=MockDBAPIConnection
            )
            with connection.cursor() as cursor:
                cursor.execute("traced")
                cursor.executemany("traced")
                cursor.callproc("traced")

        assert not tracer.finished_spans()

    def test_uninstrumented_connections_no_longer_traces(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "connection", MockDBAPIConnection):
            with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
                instrument(tracer)
                connection = psycopg2.connect("dbname=test")
                with connection.cursor() as cursor:
                    cursor.execute("traced")
                    cursor.executemany("traced")
                    cursor.callproc("traced")

                spans = tracer.finished_spans()
                assert len(spans) == 3
                for span in spans:
                    assert span.tags[tags.DATABASE_TYPE] == "PostgreSQL"
                    assert span.tags[tags.DATABASE_INSTANCE] == "test"

                assert spans[0].operation_name == "MockDBAPICursor.execute(traced)"
                assert spans[1].operation_name == "MockDBAPICursor.executemany(traced)"
                assert spans[2].operation_name == "MockDBAPICursor.callproc(traced)"

                uninstrument()
                tracer.reset()

                connection = psycopg2.connect(
                    "dbname=test", connection_factory=MockDBAPIConnection
                )
                with connection.cursor() as cursor:
                    cursor.execute("traced")
                    cursor.executemany("traced")
                    cursor.callproc("traced")

                assert not tracer.finished_spans()


class TestPsycopg2Config(Psycopg2TestSuite):
    def test_global_tracer_used_by_default(self):
        tracer = MockTracer()
        opentracing.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
            instrument()
            connection = psycopg2.connect(
                "dbname=test", connection_factory=MockDBAPIConnection
            )
            with connection.cursor() as cursor:
                cursor.execute("traced")
                cursor.executemany("traced")
                cursor.callproc("traced")

        spans = tracer.finished_spans()
        assert len(spans) == 3
        assert spans[0].operation_name == "MockDBAPICursor.execute(traced)"
        assert spans[1].operation_name == "MockDBAPICursor.executemany(traced)"
        assert spans[2].operation_name == "MockDBAPICursor.callproc(traced)"

    def test_cursor_commands_are_traced_by_default(self):
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "connection", MockDBAPIConnection):
            with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
                instrument()
                connection = psycopg2.connect("dbname=test")
                with connection.cursor() as cursor:
                    cursor.execute("traced")
                    cursor.executemany("traced")
                    cursor.callproc("traced")

        spans = tracer.finished_spans()
        assert len(spans) == 3
        assert spans[0].operation_name == "MockDBAPICursor.execute(traced)"
        assert spans[1].operation_name == "MockDBAPICursor.executemany(traced)"
        assert spans[2].operation_name == "MockDBAPICursor.callproc(traced)"

    def test_undesired_cursor_commands_are_not_traced(self):
        config.traced_commands = ["execute"]
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "connection", MockDBAPIConnection):
            with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
                instrument()
                connection = psycopg2.connect(
                    "dbname=test", connection_factory=MockDBAPIConnection
                )
                with connection.cursor() as cursor:
                    cursor.executemany("untraced")
                    cursor.callproc("untraced")
                    cursor.execute("traced")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "MockDBAPICursor.execute(traced)"

    def test_connection_commands_are_traced_by_default(self):
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "connection", MockDBAPIConnection):
            with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
                with mock.patch.object(
                    psycopg2.extensions.cursor, "callproc", side_effect=Exception
                ) as callproc:
                    callproc.__name__ = "callproc"

                    instrument()
                    connection = psycopg2.connect(
                        "dbname=test", connection_factory=MockDBAPIConnection
                    )
                    with connection as cursor:
                        cursor.execute("traced")

                    spans = tracer.finished_spans()
                    assert len(spans) == 2
                    assert spans[0].operation_name == "MockDBAPICursor.execute(traced)"
                    assert spans[1].operation_name == "MockDBAPIConnection.commit()"

                    tracer.reset()
                    with connection as cursor:
                        cursor.callproc("traced")

                    spans = tracer.finished_spans()
                    assert len(spans) == 2
                    assert spans[0].operation_name == "MockDBAPICursor.callproc(traced)"
                    assert spans[1].operation_name == "MockDBAPIConnection.rollback()"

    def test_undesired_connection_commands_are_not_traced(self):
        config.traced_commands = ["rollback"]
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(psycopg2.extensions, "connection", MockDBAPIConnection):
            with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
                with mock.patch.object(
                    psycopg2.extensions.cursor, "callproc", side_effect=Exception
                ) as callproc:
                    callproc.__name__ = "callproc"

                    instrument()
                    connection = psycopg2.connect(
                        "dbname=test", connection_factory=MockDBAPIConnection
                    )
                    with connection as cursor:
                        cursor.executemany("untraced")
                        cursor.execute("traced")

                    assert not tracer.finished_spans()

                    with connection as cursor:
                        cursor.callproc("untraced")

                    spans = tracer.finished_spans()
                    assert len(spans) == 1
                    assert spans[0].operation_name == "MockDBAPIConnection.rollback()"

    def test_span_tags_are_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.span_tags = dict(custom="tag")

        with mock.patch.object(psycopg2.extensions, "connection", MockDBAPIConnection):
            with mock.patch.object(psycopg2.extensions, "cursor", MockDBAPICursor):
                instrument()
                connection = psycopg2.connect(
                    "dbname=test", connection_factory=MockDBAPIConnection
                )
                with connection as cursor:
                    cursor.executemany("traced")
                    cursor.execute("traced")

                spans = tracer.finished_spans()
                assert len(spans) == 3
                assert spans[0].operation_name == "MockDBAPICursor.executemany(traced)"
                assert spans[1].operation_name == "MockDBAPICursor.execute(traced)"
                assert spans[2].operation_name == "MockDBAPIConnection.commit()"
                for span in spans:
                    assert span.tags["custom"] == "tag"
