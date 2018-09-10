# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from time import sleep

from opentracing.mocktracer import MockTracer
from threading import Thread
import requests
import pytest
import six

from signalfx_tracing.libraries import flask_config
from signalfx_tracing import auto_instrument


app_endpoint = 'http://127.0.0.1:32321/hello/MyName'
bp_endpoint = 'http://127.0.0.1:32321/bp/MyPage'


class TestFlaskApp(object):

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

        flask_config.traced_attributes = ['path', 'method', 'query_string', 'blueprint']

        auto_instrument(tracer)

        from .app import app
        cls._app_store[0] = app

        app_thread = Thread(target=cls.run_app)
        app_thread.daemon = True
        app_thread.start()

        for i in range(20):  # Wait for application to accept connections.
            try:
                requests.get(app_endpoint)
                break
            except Exception:
                if i == 19:
                    raise
                sleep(.25)

        tracer.reset()

        yield

    @classmethod
    def run_app(cls):
        cls._app_store[0].run(host='127.0.0.1', port=32321)

    @pytest.fixture(autouse=True)
    def reset_tracer(self):
        yield
        self.tracer.reset()

    @pytest.mark.parametrize('http_method', ('get', 'head', 'post', 'delete',
                                             'patch', 'put', 'options'))
    def test_traced_app_request(self, http_method):
        query = 'one=1&two=2'
        method = getattr(requests, http_method)
        assert method('{}?{}'.format(app_endpoint, query)).status_code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        span = spans.pop()
        assert span.operation_name == 'my_route'
        tagged_method = http_method.upper()
        expected_query_string = query if six.PY2 else str(bytes(query, 'ascii'))
        assert span.tags == {'method': tagged_method,
                             'path': '/hello/MyName',
                             'query_string': expected_query_string,
                             'blueprint': 'None',
                             'Extract failed': ''}

    @pytest.mark.parametrize('http_method', ('get', 'head', 'post', 'delete',
                                             'patch', 'put', 'options'))
    def test_traced_blueprint_request(self, http_method):
        query = 'one=1&two=2'
        method = getattr(requests, http_method)
        assert method('{}?{}'.format(bp_endpoint, query)).status_code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        span = spans.pop()
        assert span.operation_name == 'MyBlueprint.my_blueprint_route'
        tagged_method = http_method.upper()
        expected_query_string = query if six.PY2 else str(bytes(query, 'ascii'))
        assert span.tags == {'method': tagged_method,
                             'path': '/bp/MyPage',
                             'query_string': expected_query_string,
                             'blueprint': 'MyBlueprint',
                             'Extract failed': ''}
