# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from random import randint

from opentracing.mocktracer import MockTracer
from six import text_type, unichr
from opentracing.ext import tags
from pymongo import MongoClient
import docker
import pytest

from signalfx_tracing import instrument
from signalfx_tracing.libraries import pymongo_config


@pytest.fixture(scope='session')
def mongo_container():
    client = docker.from_env()
    mongo = client.containers.run('mongo:latest', ports={'27017/tcp': 27017}, detach=True)
    try:
        yield mongo
    finally:
        mongo.remove(force=True, v=True)


class TestPyMongo(object):

    _min = int('0x2700', 16)
    _max = int('0x27bf', 16)

    def random_string(self):
        """Returns a valid unicode field name"""
        rands = []
        while len(rands) < 10:
            rand = randint(self._min, self._max)
            if rand not in (0, 36, 46):
                rands.append(rand)
        return text_type('').join(unichr(i) for i in rands)

    def namespace(self, db_name, collection_name):
        return text_type('{}.{}').format(db_name, collection_name)

    @pytest.fixture
    def command_tracing(self, mongo_container):
        tracer = MockTracer()
        pymongo_config.tracer = tracer
        pymongo_config.span_tags = dict(custom='tag')
        instrument(pymongo=True)
        return tracer, MongoClient()

    def test_insert_many_sanity(self, command_tracing):
        tracer, client = command_tracing
        db_name = self.random_string()
        collection_name = self.random_string()
        collection = client[db_name][collection_name]
        docs = [{self.random_string(): self.random_string() for _ in range(5)} for __ in range(5)]
        collection.insert_many(docs)
        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.operation_name == 'insert'
        assert span.tags['namespace'] == self.namespace(db_name, collection_name)
        assert span.tags['custom'] == 'tag'
        assert span.tags['command.name'] == 'insert'
        assert span.tags[tags.COMPONENT] == 'PyMongo'
        assert span.tags['reported_duration']
        assert span.tags['event.reply']
        assert tags.ERROR not in span.tags
        assert 'event.failure' not in span.tags
