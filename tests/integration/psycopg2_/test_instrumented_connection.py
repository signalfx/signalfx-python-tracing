# Copyright (C) 2019 SignalFx, Inc. All rights reserved.
from random import choice, random, randint
from datetime import datetime
from time import sleep
import os.path
import string

from opentracing.mocktracer import MockTracer
from psycopg2.extras import DictCursor
from opentracing.ext import tags
import psycopg2
import docker
import pytest

from signalfx_tracing.libraries import psycopg2_config
from signalfx_tracing import instrument


@pytest.fixture(scope='session')
def postgres_container():
    client = docker.from_env()
    env = dict(POSTGRES_USER='postgres', POSTGRES_PASSWORD='pass', POSTGRES_DB='test_db')
    cwd = os.path.dirname(os.path.abspath(__file__))
    initdb_d = os.path.join(cwd, 'initdb.d')
    volumes = ['{}:/docker-entrypoint-initdb.d'.format(initdb_d)]
    postgres = client.containers.run('postgres:latest', environment=env, ports={'5432/tcp': 5432},
                                     volumes=volumes, detach=True)
    try:
        yield postgres
    finally:
        postgres.remove(v=True, force=True)


class TestInstrumentedConnection(object):

    def fmt_time(self, ts):
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    _strings = set()
    _ints = set()
    _floats = set()

    def random_string(self):
        while True:
            s = ''.join(choice(string.ascii_lowercase) for _ in range(10))
            if s not in self._strings:
                self._strings.add(s)
                return s

    def random_int(self):
        while True:
            i = randint(0, 100000)
            if i not in self._ints:
                self._ints.add(i)
                return i

    def random_float(self):
        while True:
            i = random() * 100000
            if i not in self._floats:
                self._floats.add(i)
                return i

    @pytest.fixture
    def connection_tracing(self, postgres_container):
        tracer = MockTracer()
        psycopg2_config.tracer = tracer
        psycopg2_config.span_tags = dict(some='tag')
        instrument(psycopg2=True)
        for i in range(480):
            try:
                conn = psycopg2.connect(host='127.0.0.1', user='test_user', password='test_password',
                                        dbname='test_db', port=5432, options='-c search_path=test_schema')
                break
            except psycopg2.OperationalError:
                sleep(.25)
            if i == 479:
                raise Exception('Failed to connect to Postgres: {}'.format(postgres_container.logs()))
        return tracer, conn

    def test_instrumented_sanity(self, connection_tracing):
        tracer, conn = connection_tracing
        with tracer.start_active_span('Parent'):
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute('insert into table_one values (%s, %s, %s, %s)',
                               (self.random_string(), self.random_string(),
                                datetime.now(), datetime.now()))
                cursor.execute('insert into table_two values (%s, %s, %s, %s)',
                               (self.random_int(), self.random_int(),
                                self.random_float(), self.random_float()))
            conn.commit()
        spans = tracer.finished_spans()
        assert len(spans) == 4
        first, second, commit, parent = spans
        for span in (first, second):
            assert span.operation_name == 'DictCursor.execute(insert)'
            assert span.tags['some'] == 'tag'
            assert span.tags[tags.DATABASE_TYPE] == 'PostgreSQL'
            assert span.tags['db.rows_produced'] == 1
            assert span.parent_id == parent.context.span_id
            assert tags.ERROR not in span.tags
        assert first.tags[tags.DATABASE_STATEMENT] == 'insert into table_one values (%s, %s, %s, %s)'
        assert second.tags[tags.DATABASE_STATEMENT] == 'insert into table_two values (%s, %s, %s, %s)'
        assert commit.operation_name == 'connection.commit()'
        assert parent.operation_name == 'Parent'
