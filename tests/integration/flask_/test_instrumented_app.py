# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from time import sleep

from flask_opentracing import FlaskScopeManager
from opentracing.mocktracer import MockTracer
from threading import Thread
import opentracing
import requests
import pytest
import six

from signalfx_tracing.libraries import flask_config
from signalfx_tracing import instrument

base_url = 'http://127.0.0.1:32321/'
app_endpoint = '{0}hello/MyName'.format(base_url)
bp_endpoint = '{0}bp/MyPage'.format(base_url)
traced_endpoint = '{0}traced'.format(base_url)


class TestFlaskApp(object):
    _app_store = [None]  # pytest doesn't persist attributes set in class-scoped autouse
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
        tracer = MockTracer(scope_manager=FlaskScopeManager())
        opentracing.tracer = tracer
        cls._tracer_store[0] = tracer

        flask_config.traced_attributes = ['path', 'method', 'query_string', 'blueprint']

        instrument(tracer, flask=True)

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
        expected_tags = {'blueprint': 'None',
                         'component': 'Flask',
                         'http.method': tagged_method,
                         'http.status_code': 200,
                         'http.url': app_endpoint,
                         'method': tagged_method,
                         'path': '/hello/MyName',
                         'query_string': expected_query_string,
                         'span.kind': 'server'}
        if http_method != 'options':
            expected_tags['handled'] = 'tag'
        assert span.tags == expected_tags

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
        expected_tags = {'blueprint': 'MyBlueprint',
                         'component': 'Flask',
                         'http.method': tagged_method,
                         'http.status_code': 200,
                         'http.url': bp_endpoint,
                         'method': tagged_method,
                         'path': '/bp/MyPage',
                         'query_string': expected_query_string,
                         'span.kind': 'server'}
        if http_method != 'options':
            expected_tags['handled'] = 'tag'
        assert span.tags == expected_tags

    def test_traced_helper(self):  # piggyback integration test for trace decorator
        assert requests.get(traced_endpoint).status_code == 200
        spans = self.tracer.finished_spans()
        assert len(spans) == 2
        child, parent = spans

        assert child.tags == dict(one=1, two=2)
        assert child.operation_name == 'myTracedHelper'
        assert child.context.trace_id == parent.context.trace_id
        assert child.parent_id == parent.context.span_id

        assert parent.operation_name == 'my_traced_route'
        expected_tags = {'blueprint': 'None',
                         'component': 'Flask',
                         'http.method': 'GET',
                         'http.status_code': 200,
                         'http.url': traced_endpoint,
                         'method': 'GET',
                         'path': '/traced',
                         'span.kind': 'server',
                         'handled': 'tag'}
        if six.PY3:  # https://github.com/opentracing-contrib/python-flask/pull/28
            expected_tags['query_string'] = "b''"
        assert parent.tags == expected_tags
