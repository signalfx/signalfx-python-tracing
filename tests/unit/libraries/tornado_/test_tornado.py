# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from tornado.testing import AsyncHTTPTestCase
from opentracing.mocktracer import MockTracer
from opentracing.ext import tags
import tornado.web
import opentracing
import pytest
import mock

from signalfx_tracing.libraries.tornado_.instrument import config, instrument, uninstrument
from .conftest import TornadoTestSuite


class MockApplication(mock.MagicMock):

    def __init__(self, *args, **kwargs):
        super(MockApplication, self).__init__(*args, **kwargs)
        self.settings = kwargs


def start_span_cb(*args, **kwargs):
    pass


class TestTornadoConfig(TornadoTestSuite):

    @pytest.mark.parametrize('trace_all, trace_client, traced_attributes, start_span_cb',
                             [(True, True, ['attr_one', 'attr_two'], None),
                              (False, False, [], start_span_cb)])
    def test_instrument_tornado_values_set_by_config(self, trace_all, trace_client, traced_attributes, start_span_cb):
        tracer = MockTracer()
        config.tracer = tracer
        config.trace_all = trace_all
        config.trace_client = trace_client
        config.traced_attributes = traced_attributes
        config.start_span_cb = start_span_cb
        with mock.patch('tornado.web.Application', MockApplication):
            instrument()
            app = MockApplication('arg1', named_arg='arg2')
            assert app.settings.get('opentracing_trace_all') is trace_all
            assert app.settings.get('opentracing_trace_client') is trace_client
            assert app.settings.get('opentracing_traced_attributes') is traced_attributes
            assert app.settings.get('opentracing_start_span_cb') is start_span_cb
            assert app.settings.get('opentracing_tracing').tracer is tracer

    def test_instrument_uses_global_tracer_without_config_tracer(self):
        config.tracer = None
        with mock.patch('tornado.web.Application', MockApplication):
            instrument()
            app = MockApplication()
            assert app.settings.get('opentracing_tracing').tracer is opentracing.tracer


class Handler(tornado.web.RequestHandler):

    def get(self):
        self.write('{}')


class TestTornadoApplicationAndClient(AsyncHTTPTestCase, TornadoTestSuite):

    def get_app(self):
        self.tracer = MockTracer()
        config.tracer = self.tracer
        instrument()
        return tornado.web.Application([('/endpoint', Handler)])

    def test_instrument_application_and_client(self):
        self.http_client.fetch(self.get_url('/endpoint'), self.stop)

        response = self.wait()
        assert response.code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 2
        assert all([span.finished for span in spans])
        server_span, client_span = spans
        assert server_span.operation_name == 'Handler'
        assert server_span.tags == {'component': 'tornado',
                                    'http.url': '/endpoint',
                                    'http.method': 'GET',
                                    'http.status_code': 200,
                                    'method': 'GET',
                                    'path': '/endpoint',
                                    tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}
        assert client_span.operation_name == 'GET'
        assert client_span.tags == {'component': 'tornado',
                                    'span.kind': 'client',
                                    'http.url': self.get_url('/endpoint'),
                                    'http.method': 'GET',
                                    'http.status_code': 200}

    def test_uninstrument_application_and_client(self):
        self.http_client.fetch(self.get_url('/endpoint'), self.stop)
        response = self.wait()
        assert response.code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 2
        assert all([span.finished for span in spans])
        self.tracer.reset()
        uninstrument()

        self.http_client.fetch(self.get_url('/endpoint'), self.stop)
        response = self.wait()
        assert response.code == 200
        assert self.tracer.finished_spans() == []


class TestTornadoApplicationAndNotClient(AsyncHTTPTestCase, TornadoTestSuite):

    def get_app(self):
        self.tracer = MockTracer()
        config.tracer = self.tracer
        config.trace_client = False
        instrument()
        self.app = tornado.web.Application([('/endpoint', Handler)])
        return self.app

    def test_instrument_application_and_client(self):
        self.http_client.fetch(self.get_url('/endpoint'), self.stop)

        response = self.wait()
        assert response.code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        server_span = spans[0]
        assert server_span.finished
        assert server_span.operation_name == 'Handler'
        assert server_span.tags == {'component': 'tornado',
                                    'http.url': '/endpoint',
                                    'http.method': 'GET',
                                    'http.status_code': 200,
                                    'method': 'GET',
                                    'path': '/endpoint',
                                    tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}

    def test_uninstrument_application(self):
        self.http_client.fetch(self.get_url('/endpoint'), self.stop)
        response = self.wait()
        assert response.code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].finished
        self.tracer.reset()
        uninstrument()

        self.http_client.fetch(self.get_url('/endpoint'), self.stop)
        response = self.wait()
        assert response.code == 200
        assert self.tracer.finished_spans() == []


class TestTornadoClientAndNotApplication(AsyncHTTPTestCase, TornadoTestSuite):

    def get_app(self):
        self.tracer = MockTracer()
        config.tracer = self.tracer
        config.trace_all = False
        instrument()
        return tornado.web.Application([('/endpoint', Handler)])

    def test_instrument_application_and_client(self):
        self.http_client.fetch(self.get_url('/endpoint'), self.stop)

        response = self.wait()
        assert response.code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        client_span = spans[0]
        assert client_span.finished
        assert client_span.operation_name == 'GET'
        assert client_span.tags == {'component': 'tornado',
                                    'span.kind': 'client',
                                    'http.url': self.get_url('/endpoint'),
                                    'http.method': 'GET',
                                    'http.status_code': 200}

    def test_uninstrument_client(self):
        self.http_client.fetch(self.get_url('/endpoint'), self.stop)
        response = self.wait()
        assert response.code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].finished
        self.tracer.reset()
        uninstrument()

        self.http_client.fetch(self.get_url('/endpoint'), self.stop)
        response = self.wait()
        assert response.code == 200
        assert self.tracer.finished_spans() == []
