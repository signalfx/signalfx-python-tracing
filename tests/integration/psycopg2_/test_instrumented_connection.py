# Copyright (C) 2019 SignalFx. All rights reserved.
from datetime import datetime
from time import sleep
import os.path

from opentracing.mocktracer import MockTracer
from psycopg2.extras import DictCursor
from opentracing.ext import tags
import psycopg2.extensions
import opentracing
import psycopg2
import docker
import pytest

from signalfx_tracing.libraries import psycopg2_config
from signalfx_tracing import instrument
from tests.utils import random_int, random_string, random_float


@pytest.fixture(scope="session")
def postgres_container():
    client = docker.from_env()
    env = dict(
        POSTGRES_USER="postgres", POSTGRES_PASSWORD="pass", POSTGRES_DB="test_db"
    )
    cwd = os.path.dirname(os.path.abspath(__file__))
    initdb_d = os.path.join(cwd, "initdb.d")
    volumes = ["{}:/docker-entrypoint-initdb.d".format(initdb_d)]
    postgres = client.containers.run(
        "postgres:latest",
        environment=env,
        ports={"5432/tcp": 5432},
        volumes=volumes,
        detach=True,
    )
    try:
        yield postgres
    finally:
        postgres.remove(v=True, force=True)


class TestInstrumentedConnection(object):
    def fmt_time(self, ts):
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    @pytest.fixture
    def connection_tracing(self, postgres_container):
        tracer = MockTracer()
        psycopg2_config.tracer = tracer
        psycopg2_config.span_tags = dict(some="tag")
        instrument(psycopg2=True)
        for i in range(480):
            try:
                conn = psycopg2.connect(
                    host="127.0.0.1",
                    user="test_user",
                    password="test_password",
                    dbname="test_db",
                    port=5432,
                    options="-c search_path=test_schema",
                )
                break
            except psycopg2.OperationalError:
                sleep(0.25)
            if i == 479:
                raise Exception(
                    "Failed to connect to Postgres: {}".format(
                        postgres_container.logs()
                    )
                )
        return tracer, conn

    def test_instrumented_sanity(self, connection_tracing):
        tracer, conn = connection_tracing

        # C arg validation
        assert isinstance(conn, psycopg2.extensions.connection)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, conn)

        with tracer.start_active_span("Parent"):
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # C arg validation
                assert isinstance(cursor, psycopg2.extensions.cursor)
                psycopg2.extras.register_uuid(None, cursor)

                cursor.execute(
                    "insert into table_one values (%s, %s, %s, %s)",
                    (random_string(), random_string(), datetime.now(), datetime.now()),
                )
                cursor.execute(
                    "insert into table_two values (%s, %s, %s, %s)",
                    (
                        random_int(0, 100000),
                        random_int(0, 100000),
                        random_float(),
                        random_float(),
                    ),
                )
            conn.commit()
        spans = tracer.finished_spans()
        assert len(spans) == 4
        for span in spans[:3]:
            assert span.tags["some"] == "tag"
            assert span.tags[tags.DATABASE_TYPE] == "PostgreSQL"
            assert span.tags[tags.DATABASE_INSTANCE] == "test_db"

        first, second, commit, parent = spans
        for span in (first, second):
            assert span.operation_name == "DictCursor.execute(insert)"
            assert span.tags["db.rows_produced"] == 1
            assert span.parent_id == parent.context.span_id
            assert tags.ERROR not in span.tags
        assert (
            first.tags[tags.DATABASE_STATEMENT]
            == "insert into table_one values (%s, %s, %s, %s)"
        )
        assert (
            second.tags[tags.DATABASE_STATEMENT]
            == "insert into table_two values (%s, %s, %s, %s)"
        )
        assert commit.operation_name == "connection.commit()"
        assert parent.operation_name == "Parent"

    def test_nonclass_connection_factory_prevents_tracing(self, postgres_container):
        tracer = MockTracer()
        opentracing.tracer = tracer
        for i in range(480):
            try:
                conn = psycopg2.connect(
                    host="127.0.0.1",
                    user="test_user",
                    password="test_password",
                    dbname="test_db",
                    port=5432,
                    options="-c search_path=test_schema",
                    connection_factory=lambda dsn: psycopg2.extensions.connection(dsn),
                )
                break
            except psycopg2.OperationalError:
                sleep(0.25)
            if i == 479:
                raise Exception(
                    "Failed to connect to Postgres: {}".format(
                        postgres_container.logs()
                    )
                )

        assert isinstance(conn, psycopg2.extensions.connection)

        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                "insert into table_one values (%s, %s, %s, %s)",
                (random_string(), random_string(), datetime.now(), datetime.now()),
            )
        conn.commit()
        assert not tracer.finished_spans()
