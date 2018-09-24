# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from opentracing.mocktracer import MockTracer
from mockupdb import go
import opentracing
import pymongo

from signalfx_tracing.libraries.pymongo_.instrument import config, instrument, uninstrument
from .conftest import PyMongoTestSuite


class TestPyMongo(PyMongoTestSuite):

    def test_noninstrumented_client_does_not_trace(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        client = pymongo.MongoClient(self.server.uri)
        fut = go(client.db.collection.insert_one, dict(one=123))
        self.server.receives().ok()
        fut()

        assert not tracer.finished_spans()

    def test_uninstrumented_clients_no_longer_traces(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        instrument(tracer)
        client = pymongo.MongoClient(self.server.uri)
        fut = go(client.db.collection.insert_many, [dict(one=123), dict(two=234)])
        self.server.receives().ok()
        fut()

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'insert'

        uninstrument()
        tracer.reset()

        client = pymongo.MongoClient(self.server.uri)
        fut = go(client.db.collection.insert_many, [dict(one=123), dict(two=234)])
        self.server.receives().ok()
        fut()

        assert not tracer.finished_spans()


class TestPyMongoConfig(PyMongoTestSuite):

    def test_global_tracer_used_by_default(self):
        tracer = MockTracer()
        opentracing.tracer = tracer

        instrument(tracer)
        client = pymongo.MongoClient(self.server.uri)
        fut = go(client.db.collection.insert_many, [dict(one=123), dict(two=234)])
        self.server.receives().ok()
        fut()

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'insert'

    def test_span_tags_are_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.span_tags = dict(custom='tag')

        instrument(tracer)
        client = pymongo.MongoClient(self.server.uri)
        fut = go(client.db.collection.insert_many, [dict(one=123), dict(two=234)])
        self.server.receives().ok()
        fut()

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == 'insert'
