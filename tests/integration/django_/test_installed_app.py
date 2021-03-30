# Copyright (C) 2018 SignalFx. All rights reserved.
from django.test import SimpleTestCase, Client
from django.conf import settings
import opentracing

from signalfx_tracing.libraries.django_.instrument import (
    config,
    get_middleware_and_setting_name,
)


class TestSignalFxTracingInstalledApp(SimpleTestCase):
    def test_unset_global_tracer_installed_app_sanity(self):
        assert "signalfx_tracing" in settings.INSTALLED_APPS
        assert config.middleware_class in get_middleware_and_setting_name()[0]
        assert config.tracer_callable == "opentracing.mocktracer.MockTracer"
        assert config.tracer_parameters == dict(scope_manager=None)

        client = Client()
        client.get("/one/")
        tracer = settings.OPENTRACING_TRACING.tracer
        span = tracer.finished_spans().pop()
        assert span.tags["path"] == "/one/"
        assert span.tags["method"] == "GET"

        assert (
            settings.OPENTRACING_TRACER_CALLABLE == "opentracing.mocktracer.MockTracer"
        )
        assert settings.OPENTRACING_TRACER_PARAMETERS == dict(scope_manager=None)
        assert opentracing.tracer is not tracer
