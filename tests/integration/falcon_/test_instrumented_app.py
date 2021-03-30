# Copyright (C) 2020 SignalFx. All rights reserved.
from time import sleep

from wsgiref import simple_server

from opentracing.mocktracer import MockTracer
from threading import Thread
import requests
import pytest

from signalfx_tracing import instrument


base_url = "http://127.0.0.1:32321/"
endpoint = "{0}hello".format(base_url)
endpoint_404 = "{0}hello/xyz".format(base_url)
endpoint_500 = "{0}error".format(base_url)


def span_callback(span, request):
    span.set_tag("some_tag", True)


class TestFalconApp(object):

    _app_store = [None]  # pytest doesn't persist attributes set in class-scoped autouse
    _tracer_store = [None]  # fixtures, so use stores as a hack.

    @property
    def app(self):
        return self._app_store[0]

    @property
    def tracer(self):
        return self._tracer_store[0]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def instrumented_app(cls):
        tracer = MockTracer()
        cls._tracer_store[0] = tracer

        instrument(tracer, falcon=True)

        from .app import app

        cls._app_store[0] = app

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
                sleep(0.25)

        tracer.reset()

        yield

    @classmethod
    def run_app(cls):
        httpd = simple_server.make_server("127.0.0.1", 32321, cls._app_store[0])
        httpd.serve_forever()

    @pytest.fixture(autouse=True)
    def reset_tracer(self):
        yield
        self.tracer.reset()

    @pytest.mark.parametrize(
        "http_method", ("get", "head", "post", "delete", "patch", "put", "options")
    )
    def test_traced_app_request(self, http_method):
        query = "one=1&two=2"
        method = getattr(requests, http_method)
        assert method("{}?{}".format(endpoint, query)).status_code == 200

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        span = spans.pop()
        assert span.operation_name == "HelloWorldResource.on_{0}".format(
            http_method.lower()
        )
        tagged_method = http_method.upper()
        expected_tags = {
            "component": "Falcon",
            "http.method": tagged_method,
            "http.status_code": "200",
            "http.url": endpoint,
            "http.method": tagged_method,
            "path": "/hello",
            "span.kind": "server",
            "falcon.resource": "HelloWorldResource",
        }
        assert span.tags == expected_tags

    @pytest.mark.parametrize(
        "http_method", ("get", "head", "post", "delete", "patch", "put", "options")
    )
    def test_traced_app_request_404(self, http_method):
        query = "one=1&two=2"
        method = getattr(requests, http_method)
        assert method("{}?{}".format(endpoint_404, query)).status_code == 404

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        span = spans.pop()
        assert span.operation_name == "/hello/xyz"
        tagged_method = http_method.upper()
        expected_tags = {
            "component": "Falcon",
            "http.method": tagged_method,
            "http.status_code": "404",
            "http.url": endpoint_404,
            "http.method": tagged_method,
            "path": "/hello/xyz",
            "span.kind": "server",
        }
        assert span.tags == expected_tags

    @pytest.mark.parametrize(
        "http_method", ("get", "head", "post", "delete", "patch", "put", "options")
    )
    def test_traced_app_request_500(self, http_method):
        query = "one=1&two=2"
        method = getattr(requests, http_method)
        assert method("{}?{}".format(endpoint_500, query)).status_code == 500

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        span = spans.pop()
        assert span.operation_name == "ErrorResource.on_{0}".format(http_method.lower())
        tagged_method = http_method.upper()
        expected_tags = {
            "component": "Falcon",
            "http.method": tagged_method,
            "http.status_code": "500",
            "http.url": endpoint_500,
            "http.method": tagged_method,
            "path": "/error",
            "span.kind": "server",
            "error": True,
            "sfx.error.kind": "NameError",
            "falcon.resource": "ErrorResource",
        }

        err_message = span.tags.pop("sfx.error.message")
        err_object = span.tags.pop("sfx.error.object")
        err_stack = span.tags.pop("sfx.error.stack")
        assert span.tags == expected_tags

        assert "name 'undefined' is not defined" in err_message
        assert err_object in ("<class 'NameError'>", "<type 'exceptions.NameError'>")
        assert err_stack is not None
        assert "in _handle\n    print(undefined)" in err_stack
