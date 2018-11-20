# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from opentracing.mocktracer import MockTracer
from opentracing.ext import tags as ext_tags
import docker
import pytest
from redis import StrictRedis

from signalfx_tracing.libraries import redis_config as config
from signalfx_tracing import instrument, uninstrument


@pytest.fixture(scope='session')
def redis_container():
    session = docker.from_env()
    redis = session.containers.run('redis:latest', ports={'6379/tcp': 6379}, detach=True)
    try:
        yield redis
    finally:
        redis.remove(force=True, v=True)


class TestClientTracing(object):

    @pytest.fixture
    def client_tracing(self, redis_container):
        tracer = MockTracer()
        config.tracer = tracer

        instrument(redis=True)
        try:
            yield tracer
        finally:
            uninstrument('redis')

    @pytest.fixture
    def tracer(self, client_tracing):
        return client_tracing

    @pytest.fixture
    def client(self, client_tracing):
        return StrictRedis()

    def test_successfully_traced_command(self, tracer, client):
        with tracer.start_active_span('root'):
            client.set('key', 'val')
        spans = tracer.finished_spans()
        assert len(spans) == 2
        req_span, root_span = spans
        assert req_span.operation_name == 'SET'

        tags = req_span.tags
        assert tags[ext_tags.COMPONENT] == 'redis-py'
        assert tags[ext_tags.SPAN_KIND] == ext_tags.SPAN_KIND_RPC_CLIENT
        assert tags[ext_tags.DATABASE_TYPE] == 'redis'
        assert tags[ext_tags.DATABASE_STATEMENT] == 'SET key val'
        assert ext_tags.ERROR not in tags

    def test_successfully_traced_pubsub(self, tracer, client):
        with tracer.start_active_span('root'):
            pubsub = client.pubsub()
            pubsub.subscribe('myChannel')
            client.publish('myChannel', 'hey')
            pubsub.parse_response()
            pubsub.unsubscribe('myChannel')

            pubsub = client.pubsub()
            pubsub.subscribe('myOtherChannel')
            client.publish('myOtherChannel', 'hey')
            pubsub.parse_response()
            pubsub.unsubscribe('myOtherChannel')

        spans = tracer.finished_spans()
        assert len(spans) == 9

    def test_successfully_traced_pipeline(self, tracer, client):
        with tracer.start_active_span('root'):
            pipeline = client.pipeline()
            pipeline.set('key', 'value')
            pipeline.get('key')
            pipeline.execute()

            pipeline = client.pipeline()
            pipeline.set('another_key', 'value')
            pipeline.get('another_key')
            pipeline.execute()

        spans = tracer.finished_spans()
        assert len(spans) == 3
