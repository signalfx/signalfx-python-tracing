# Copyright (C) 2019 SignalFx. All rights reserved.
from contextlib import contextmanager

from opentracing.mocktracer import MockTracer
from elasticsearch import Elasticsearch, VERSION
from opentracing.ext import tags
from mock import patch
import opentracing

from signalfx_tracing.libraries.elasticsearch_ import config, instrument, uninstrument
from .conftest import ElasticsearchTestSuite


class TestElasticsearch(ElasticsearchTestSuite):

    body = dict(body="body")

    @contextmanager
    def mocked_transport(self):
        with patch(
            "elasticsearch.transport.Transport.perform_request"
        ) as perform_request:
            if VERSION < (5, 0, 0):
                perform_request.return_value = False, dict(some="thing")
            yield perform_request

    def test_trace_with_default_config(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        instrument()

        with self.mocked_transport() as perform_request:
            es = Elasticsearch()
            es.index(index="some-index", doc_type="some-doc-type", id=1, body=self.body)
            assert perform_request.called

        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.operation_name == "Elasticsearch/some-index/some-doc-type/1"
        assert span.tags == {
            "component": "elasticsearch-py",
            tags.DATABASE_STATEMENT: str(self.body),
            tags.DATABASE_TYPE: "elasticsearch",
            "elasticsearch.method": "PUT",
            "elasticsearch.url": "/some-index/some-doc-type/1",
            "span.kind": "client",
        }

    def test_trace_with_updated_config(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.prefix = "SomePrefix"
        instrument()

        with self.mocked_transport() as perform_request:
            es = Elasticsearch()
            es.index(index="some-index", doc_type="some-doc-type", id=1, body=self.body)
            assert perform_request.called

        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.operation_name == "SomePrefix/some-index/some-doc-type/1"
        assert span.tags == {
            "component": "elasticsearch-py",
            tags.DATABASE_STATEMENT: str(self.body),
            tags.DATABASE_TYPE: "elasticsearch",
            "elasticsearch.method": "PUT",
            "elasticsearch.url": "/some-index/some-doc-type/1",
            "span.kind": "client",
        }

    def test_uninstrument_reverts_wrapper(self):
        tracer = MockTracer()
        instrument(tracer)

        with self.mocked_transport() as perform_request:
            es = Elasticsearch()
            es.index(index="some-index", doc_type="some-doc-type", id=1, body=self.body)
            assert perform_request.called

        assert len(tracer.finished_spans()) == 1

        tracer.reset()
        uninstrument()

        with self.mocked_transport() as perform_request:
            es = Elasticsearch()
            es.index(index="some-index", doc_type="some-doc-type", id=1, body=self.body)
            assert perform_request.called

        assert not tracer.finished_spans()
