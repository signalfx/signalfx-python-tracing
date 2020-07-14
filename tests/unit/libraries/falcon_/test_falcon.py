# Copyright (C) 2020 SignalFx. All rights reserved.
import opentracing
import falcon

from falcon import testing
from opentracing.mocktracer import MockTracer

from signalfx_tracing.libraries.falcon_ import config, instrument, uninstrument
from signalfx_tracing.libraries.falcon_.middleware import TraceMiddleware
from .conftest import FalconTestSuite


class HelloWorldResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = "Hello World"


class TestFalconApplication(FalconTestSuite):
    def make_app(self):
        app = falcon.API()
        app.add_route("/hello", HelloWorldResource())
        return app

    def client(self, app):
        return testing.TestClient(app)

    def test_instrument_with_default_config(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        instrument()
        app = self.make_app()

        assert len(app._middleware) == 3

        pre = app._middleware[0][0]
        post = app._middleware[2][0]

        assert isinstance(pre.__self__, TraceMiddleware)
        assert isinstance(post.__self__, TraceMiddleware)

        middleware = pre.__self__
        assert middleware.tracer is tracer
        uninstrument()

    def test_instrument_with_custom_config(self):
        opentracing.tracer = MockTracer()
        config.tracer = MockTracer()
        instrument()
        app = self.make_app()

        assert len(app._middleware) == 3
        pre = app._middleware[0][0]

        middleware = pre.__self__
        assert middleware.tracer is config.tracer
        uninstrument()

    def test_trace_with_custom_config(self):
        tracer = MockTracer()
        instrument(tracer)
        app = self.make_app()

        client = self.client(app)
        result = client.simulate_get("/hello?qs=1")
        assert result.content == b"Hello World"

        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.operation_name == "HelloWorldResource.on_get"
        assert span.tags == {
            "component": "Falcon",
            "http.method": "GET",
            "http.status_code": "200",
            "http.url": u"http://falconframework.org/hello",
            "http.method": "GET",
            "path": "/hello",
            "span.kind": "server",
            "falcon.resource": "HelloWorldResource"
        }

    def test_uninstrument_reverts_wrapper(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        instrument()

        app = self.make_app()
        client = self.client(app)
        assert client.simulate_get("/hello").status_code == 200
        assert len(tracer.finished_spans()) == 1

        tracer.reset()
        uninstrument()

        app = self.make_app()
        client = self.client(app)
        assert client.simulate_get("/hello").status_code == 200
        assert tracer.finished_spans() == []
