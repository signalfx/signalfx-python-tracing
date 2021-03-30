# Copyright (C) 2018 SignalFx. All rights reserved.
from opentracing.mocktracer import MockTracer
import opentracing
import requests
import mock

from signalfx_tracing.libraries.requests_.instrument import (
    config,
    instrument,
    uninstrument,
)
from requests_opentracing import SessionTracing
from .conftest import RequestsTestSuite


class MockResponse(object):
    def __init__(self, method, url, headers=None):
        self.method = method
        self.url = url
        self.status_code = 200
        self.headers = headers or {}


def mocked_request(self, method, url, *args, **kwargs):
    return MockResponse(method, url, kwargs.get("headers"))


class TestRequestsConfig(RequestsTestSuite):
    def test_global_tracer_used_by_default(self):
        tracer = MockTracer()
        opentracing.tracer = tracer

        instrument()
        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            session.get("some_url")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "requests.get"

    def test_tracer_is_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer

        instrument()
        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            session.get("some_url")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "requests.get"

    def test_propagate_is_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer

        instrument()
        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            response = session.get("some_url")
        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert "ot-trace-spanid" not in response.headers
        assert "ot-trace-traceid" not in response.headers

        tracer.reset()
        config.propagate = True
        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            response = session.get("some_url")
        spans = tracer.finished_spans()

        assert len(spans) == 1
        span = spans[0]
        assert response.headers["ot-tracer-spanid"] == "{0:x}".format(
            span.context.span_id
        )
        assert response.headers["ot-tracer-traceid"] == "{0:x}".format(
            span.context.trace_id
        )

    def test_span_tags_are_sourced(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.span_tags = dict(some="tag")

        instrument()
        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            session.get("some_url")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags["some"] == "tag"

    def test_custom_requests_session(self):
        class CustomSession(requests.Session):
            _requests_made = []

            def custom_get(self, url):
                return self.get(url)

            def request(self, method, url, *args, **kwargs):
                self._requests_made.append((args, kwargs))
                return MockResponse(method, url, kwargs.get("headers"))

        tracer = MockTracer()
        config.tracer = tracer
        config.span_tags = dict(some="tag")

        instrument()
        session = CustomSession()
        assert isinstance(session, CustomSession)
        assert isinstance(session, requests.Session)
        assert isinstance(session, SessionTracing)

        session.custom_get("some_url")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags["some"] == "tag"

    def test_custom_requests_session_super(self):
        class CustomSession(requests.Session):
            _requests_made = []

            def custom_get(self, url):
                return self.get(url)

            def request(self, *args, **kwargs):
                self._requests_made.append((args, kwargs))
                return super(CustomSession, self).request(*args, **kwargs)

        tracer = MockTracer()
        config.tracer = tracer
        config.span_tags = dict(some="tag")

        instrument()
        session = CustomSession()
        assert isinstance(session, CustomSession)
        assert isinstance(session, requests.Session)
        assert isinstance(session, SessionTracing)

        with mock.patch.object(requests.Session, "request", mocked_request):
            session.custom_get("some_url")

        assert len(session._requests_made) == 1
        args, _ = session._requests_made[0]
        assert args == ("GET", "some_url")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].tags["some"] == "tag"


class TestRequests(RequestsTestSuite):
    def test_noninstrumented_client_does_not_trace(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            session.get("some_url")

        assert not tracer.finished_spans()

    def test_uninstrumented_clients_no_longer_traces(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        config.tracer = tracer

        instrument(tracer)
        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            session.get("some_url")

        spans = tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "requests.get"

        uninstrument()
        tracer.reset()

        session = requests.Session()
        with mock.patch.object(requests.Session, "request", mocked_request):
            session.get("some_url")

        assert not tracer.finished_spans()
