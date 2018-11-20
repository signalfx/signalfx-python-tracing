# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from opentracing.mocktracer import MockTracer
import opentracing
import redis
import mock

from signalfx_tracing.libraries.redis_.instrument import config, instrument, uninstrument
from .conftest import RedisTestSuite


def mock_execute_command(*args, **kwargs):
    return True


class TestRedisConfig(RedisTestSuite):

    def test_global_tracer_used_by_default(self):
        tracer = MockTracer()
        opentracing.tracer = tracer

        with mock.patch.object(redis.StrictRedis, 'execute_command', mock_execute_command):
            instrument()
            client = redis.StrictRedis()
            client.set('key', 'value')

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'SET'

    def test_tracer_is_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer

        with mock.patch.object(redis.StrictRedis, 'execute_command', mock_execute_command):
            instrument()
            client = redis.StrictRedis()
            client.get('key')

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'GET'


class TestRedis(RedisTestSuite):

    def test_noninstrumented_client_does_not_trace(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        client = redis.StrictRedis()
        with mock.patch.object(redis.StrictRedis, 'execute_command', mock_execute_command):
            client.get('some_url')

        assert not tracer.finished_spans()

    def test_uninstrumented_clients_no_longer_traces(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        with mock.patch.object(redis.StrictRedis, 'execute_command', mock_execute_command):
            instrument(tracer)
            client = redis.StrictRedis()
            client.get('some_url')

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'GET'

        uninstrument()
        tracer.reset()

        client = redis.StrictRedis()
        with mock.patch.object(redis.StrictRedis, 'execute_command', mock_execute_command):
            client.get('some_url')

        assert not tracer.finished_spans()
