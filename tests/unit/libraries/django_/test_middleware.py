# Copyright (C) 2018 SignalFx. All rights reserved.
from django.test import SimpleTestCase, Client
from opentracing.mocktracer import MockTracer
from django.conf import settings
import opentracing
import mock

from signalfx_tracing.libraries.django_.instrument import (
    config,
    get_middleware_and_setting_name,
)
from signalfx_tracing import instrument

from .conftest import DjangoTestSuite


class TestDjangoOpenTracingMiddleware(SimpleTestCase, DjangoTestSuite):
    def test_set_global_tracer_middleware_sanity(self):
        config.set_global_tracer = True
        config.tracer_callable = "opentracing.mocktracer.MockTracer"
        config.tracer_parameters = dict(scope_manager=None)
        instrument(django=True)

        client = Client()
        client.get("/one/")
        tracer = opentracing.tracer
        span = tracer.finished_spans().pop()

        assert span.tags["path"] == "/one/"
        assert span.tags["method"] == "GET"

        assert settings.OPENTRACING_TRACER_CALLABLE == config.tracer_callable
        assert settings.OPENTRACING_TRACER_PARAMETERS == dict(scope_manager=None)
        assert settings.OPENTRACING_TRACER._tracer is opentracing.tracer

    def test_unset_global_tracer_middleware_sanity(self):
        config.set_global_tracer = False
        tracer = MockTracer()
        instrument(tracer, django=True)
        client = Client()
        client.get("/one/")

        span = tracer.finished_spans().pop()
        assert span.tags["path"] == "/one/"
        assert span.tags["method"] == "GET"

        assert not hasattr(settings, "OPENTRACING_TRACER_CALLABLE")
        assert not hasattr(settings, "OPENTRACING_TRACER_PARAMETERS")
        assert settings.OPENTRACING_TRACER.tracer is tracer
        assert opentracing.tracer is not tracer

    def test_middleware_untraced(self):
        client = Client()
        with mock.patch("opentracing.span.Span.set_tag") as set_tag:
            client.get("/one/")
            assert set_tag.called is False

        assert not hasattr(settings, "OPENTRACING_TRACED_ATTRIBUTES")
        assert not hasattr(settings, "OPENTRACING_TRACER_CALLABLE")
        assert not hasattr(settings, "OPENTRACING_TRACER_PARAMETERS")
        assert not hasattr(settings, "OPENTRACING_TRACE_ALL")
        assert not hasattr(settings, "OPENTRACING_SET_GLOBAL_TRACER")
        assert not hasattr(settings, "OPENTRACING_TRACING")
        assert not hasattr(settings, "OPENTRACING_TRACER")
        _, setting = get_middleware_and_setting_name()
        assert config.middleware_class not in getattr(settings, setting)
