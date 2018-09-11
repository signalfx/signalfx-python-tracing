# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from django.test import SimpleTestCase, Client
from django.conf import settings
import opentracing

from signalfx_tracing.libraries.django_.instrument import config, get_middleware_and_setting_name


class TestSignalFxTracingInstalledApp(SimpleTestCase):

    def test_set_global_tracer_installed_app_sanity(self):
        assert 'signalfx_tracing' in settings.INSTALLED_APPS
        assert config.middleware_class in get_middleware_and_setting_name()[0]
        config.tracer_callable = 'opentracing.mocktracer.MockTracer'

        client = Client()
        client.get('/one/')
        tracer = opentracing.tracer
        span = tracer.finished_spans().pop()
        span.tags['path'] = '/one/'
        span.tags['method'] = 'GET'

        assert settings.OPENTRACING_TRACER_CALLABLE == config.tracer_callable
        assert settings.OPENTRACING_TRACER_PARAMETERS == config.tracer_parameters
        assert settings.OPENTRACING_TRACER._tracer is opentracing.tracer
