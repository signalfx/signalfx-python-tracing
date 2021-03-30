# Copyright (C) 2018-2019 SignalFx. All rights reserved.
from datetime import datetime
from time import sleep
import os.path

from opentracing.mocktracer import MockTracer
from pymysql.cursors import DictCursor
from opentracing.ext import tags
import pymysql
import docker
import pytest

from signalfx_tracing.libraries import pymysql_config
from signalfx_tracing import instrument
from tests.utils import random_int, random_float, random_string


@pytest.fixture(scope="session")
def mysql_container():
    client = docker.from_env()
    env = dict(MYSQL_ROOT_PASSWORD="pass", MYSQL_ROOT_HOST="%")
    cwd = os.path.dirname(os.path.abspath(__file__))
    conf_d = os.path.join(cwd, "conf.d")
    initdb_d = os.path.join(cwd, "initdb.d")
    volumes = [
        "{}:/etc/mysql/conf.d".format(conf_d),
        "{}:/docker-entrypoint-initdb.d".format(initdb_d),
    ]
    mysql = client.containers.run(
        "mysql:latest",
        environment=env,
        ports={"3306/tcp": 3306},
        volumes=volumes,
        detach=True,
    )
    try:
        yield mysql
    finally:
        mysql.remove(v=True, force=True)


class TestInstrumentedConnection(object):
    def fmt_time(self, ts):
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    @pytest.fixture
    def connection_tracing(self, mysql_container):
        tracer = MockTracer()
        pymysql_config.tracer = tracer
        pymysql_config.span_tags = dict(some="tag")
        instrument(pymysql=True)
        for i in range(480):
            try:
                conn = pymysql.connect(
                    host="127.0.0.1",
                    user="test_user",
                    password="test_password",
                    db="test_db",
                    port=3306,
                    cursorclass=DictCursor,
                )
                break
            except pymysql.OperationalError:
                sleep(0.25)
            if i == 479:
                raise Exception(
                    "Failed to connect to MySQL: {}".format(mysql_container.logs())
                )
        return tracer, conn

    def test_instrumented_sanity(self, connection_tracing):
        tracer, conn = connection_tracing
        with tracer.start_active_span("Parent"):
            with conn.cursor() as cursor:
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
            assert span.tags[tags.DATABASE_TYPE] == "MySQL"
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
        assert commit.operation_name == "Connection.commit()"
        assert parent.operation_name == "Parent"
