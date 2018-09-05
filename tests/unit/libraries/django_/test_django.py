# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from django.conf import settings
import opentracing
import pytest
import mock

from signalfx_tracing.libraries.django_.instrument import config, get_middleware_and_setting_name
from signalfx_tracing.instrumentation import instrument, uninstrument
from signalfx_tracing.utils import Config
from .conftest import DjangoTestSuite


class TestDjangoConfig(DjangoTestSuite):

    @pytest.mark.parametrize('version, expected_setting',
                             [((1, 1), 'MIDDLEWARE_CLASSES'),
                              ((1, 9), 'MIDDLEWARE_CLASSES'),
                              ((1, 10), 'MIDDLEWARE_CLASSES'),
                              ((1, 11), 'MIDDLEWARE'),
                              ((2, 0), 'MIDDLEWARE')])
    def test_get_middleware_returns_desired_object_and_setting(self, version, expected_setting):
        expected_middleware = ['Middlware']
        settings_stub = Config()
        setattr(settings_stub, expected_setting, expected_middleware)
        with mock.patch('django.VERSION', version):
            with mock.patch('django.conf.settings', settings_stub):
                middleware, setting = get_middleware_and_setting_name()
                assert middleware == expected_middleware
                assert setting == expected_setting

    def test_instrument_django_set_global_tracer_configures_desired_settings(self):
        config.set_global_tracer = True
        instrument(opentracing.tracer, django=True)

        assert settings.OPENTRACING_SET_GLOBAL_TRACER is True
        assert settings.OPENTRACING_TRACER_CALLABLE == config.tracer_callable
        assert settings.OPENTRACING_TRACER_PARAMETERS == config.tracer_parameters
        assert not hasattr(settings, 'OPENTRACING_TRACER')

        assert settings.OPENTRACING_TRACE_ALL == config.trace_all
        assert settings.OPENTRACING_TRACED_ATTRIBUTES == config.traced_attributes
        _, setting = get_middleware_and_setting_name()
        assert config.middleware_class in getattr(settings, setting)

    def test_instrument_django_unset_global_tracer_configures_desired_settings(self):
        config.set_global_tracer = False
        instrument(opentracing.tracer, django=True)

        assert settings.OPENTRACING_SET_GLOBAL_TRACER is False
        assert isinstance(settings.OPENTRACING_TRACER._tracer, opentracing.Tracer)
        assert not hasattr(settings, 'OPENTRACING_TRACER_CALLABLE')
        assert not hasattr(settings, 'OPENTRACING_TRACER_PARAMETERS')

        assert settings.OPENTRACING_TRACE_ALL == config.trace_all
        assert settings.OPENTRACING_TRACED_ATTRIBUTES == config.traced_attributes
        _, setting = get_middleware_and_setting_name()
        assert config.middleware_class in getattr(settings, setting)

    def test_uninstrument_django_removes_configured_settings(self):
        instrument(django=True)
        uninstrument('django')
        assert not hasattr(settings, 'OPENTRACING_TRACED_ATTRIBUTES')
        assert not hasattr(settings, 'OPENTRACING_TRACER_CALLABLE')
        assert not hasattr(settings, 'OPENTRACING_TRACER_PARAMETERS')
        assert not hasattr(settings, 'OPENTRACING_TRACE_ALL')
        assert not hasattr(settings, 'OPENTRACING_SET_GLOBAL_TRACER')
        assert not hasattr(settings, 'OPENTRACING_TRACER')
        _, setting = get_middleware_and_setting_name()
        assert config.middleware_class not in getattr(settings, setting)

    def test_django_config_determines_instrumented_setting_values_with_global_tracer(self):
        config.set_global_tracer = True
        desired_attributes = ['some', 'attributes']
        config.traced_attributes = desired_attributes
        desired_callable = 'some.callable'
        config.tracer_callable = desired_callable
        desired_trace_all = 123
        config.trace_all = desired_trace_all
        desired_middleware_class = 'some.middleware'
        config.middleware_class = desired_middleware_class

        instrument(django=True)
        assert settings.OPENTRACING_TRACED_ATTRIBUTES == desired_attributes
        assert settings.OPENTRACING_TRACER_CALLABLE == desired_callable
        assert settings.OPENTRACING_TRACE_ALL == desired_trace_all
        _, setting = get_middleware_and_setting_name()
        assert config.middleware_class in getattr(settings, setting)

        uninstrument('django')
        assert not hasattr(settings, 'OPENTRACING_TRACED_ATTRIBUTES')
        assert not hasattr(settings, 'OPENTRACING_TRACER_CALLABLE')
        assert not hasattr(settings, 'OPENTRACING_TRACE_ALL')
        assert desired_middleware_class not in getattr(settings, setting)

    def test_django_config_determines_instrumented_setting_values_without_global_tracer(self):
        config.set_global_tracer = False
        desired_attributes = ['some', 'attributes']
        config.traced_attributes = desired_attributes
        desired_trace_all = 123
        config.trace_all = desired_trace_all
        desired_middleware_class = 'some.middleware'
        config.middleware_class = desired_middleware_class

        tracer = 'SomeTracer'
        instrument(tracer, django=True)
        assert settings.OPENTRACING_TRACER._tracer is tracer
        assert settings.OPENTRACING_TRACED_ATTRIBUTES == desired_attributes
        assert settings.OPENTRACING_TRACE_ALL == desired_trace_all
        _, setting = get_middleware_and_setting_name()
        assert desired_middleware_class in getattr(settings, setting)

        uninstrument('django')
        assert not hasattr(settings, 'OPENTRACING_TRACED_ATTRIBUTES')
        assert not hasattr(settings, 'OPENTRACING_TRACER_CALLABLE')
        assert not hasattr(settings, 'OPENTRACING_TRACE_ALL')
        assert desired_middleware_class not in getattr(settings, setting)
