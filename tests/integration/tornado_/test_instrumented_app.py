# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from time import sleep

from opentracing.mocktracer import MockTracer
from tornado.ioloop import IOLoop
from opentracing.ext import tags
from threading import Thread
import requests
import tornado
import pytest
import six

from signalfx_tracing.libraries import tornado_config
from signalfx_tracing import instrument
from .app import MyApplication, HelloHandler


endpoint = 'http://127.0.0.1:32321/hello/MyName'


def span_callback(span, request):
    span.set_tag('some_tag', True)


class TestTornadoApp(object):

    _app_store = [None]     # pytest doesn't persist attributes set in class-scoped autouse
    _tracer_store = [None]  # fixtures, so use stores as a hack.

    @property
    def app(self):
        return self._app_store[0]

    @property
    def tracer(self):
        return self._tracer_store[0]

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def instrumented_app(cls):
        tracer = MockTracer()
        cls._tracer_store[0] = tracer

        tornado_config.start_span_cb = span_callback
        tornado_config.traced_attributes = ['path', 'method', 'query']

        instrument(tracer, tornado=True)

        cls._app_store[0] = MyApplication([(r'/hello/(.*)', HelloHandler)])
        app_thread = Thread(target=cls.run_app)
        app_thread.daemon = True
        app_thread.start()

        for i in range(20):  # Wait for application to accept connections.
            try:
                requests.get(endpoint)
                break
            except Exception:
                if i == 19:
                    raise
                sleep(.25)

        tracer.reset()

        yield

        def stop_ioloop():
            IOLoop.current().stop()

        IOLoop.current().add_callback(stop_ioloop)

    @classmethod
    def run_app(cls):
        if six.PY3 and tornado.version_info >= (5, 0):
            import asyncio
            asyncio.set_event_loop(asyncio.new_event_loop())

        cls._app_store[0].listen(32321)
        IOLoop.current().start()
        IOLoop.current().close()

    @pytest.fixture(autouse=True)
    def reset_tracer(self):
        yield
        self.tracer.reset()

    def test_app_settings(self):
        settings = self.app.settings
        assert settings['opentracing_tracing'].tracer is self.tracer
        assert settings['opentracing_traced_attributes'] == tornado_config.traced_attributes
        assert settings['opentracing_start_span_cb'] == tornado_config.start_span_cb
        assert settings['opentracing_trace_all'] == tornado_config.trace_all
        assert settings['opentracing_trace_client'] == tornado_config.trace_client

    @pytest.mark.parametrize('http_method', ('get', 'head', 'post', 'delete',
                                             'patch', 'put', 'options'))
    def test_traced_request(self, http_method):
        query = 'one=1&two=2'
        method = getattr(requests, http_method)
        method('{}?{}'.format(endpoint, query))

        for _ in range(20):  # Tornado's async nature makes this flakey
            if self.tracer.finished_spans():
                break
            sleep(.25)

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        span = spans.pop()
        assert span.operation_name == 'HelloHandler'
        tagged_method = http_method.upper()
        assert span.tags == {'component': 'tornado',
                             'http.url': '/hello/MyName?one=1&two=2',
                             'http.method': tagged_method,
                             'http.status_code': 200,
                             'method': tagged_method,
                             'path': '/hello/MyName',
                             'query': query,
                             'some_tag': True,
                             tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}
