# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from django.apps import AppConfig
from django.conf import settings

from .instrument import config, instrument


class SignalFxConfig(AppConfig):

    name = 'signalfx_tracing'
    verbose_name = 'SignalFx Tracing'

    def ready(self):
        if getattr(settings, 'SIGNALFX_TRACE_ALL', None) is not None:
            config.trace_all = settings.SIGNALFX_TRACE_ALL
        if getattr(settings, 'SIGNALFX_TRACED_ATTRIBUTES', None) is not None:
            config.traced_attributes = settings.SIGNALFX_TRACED_ATTRIBUTES
        if getattr(settings, 'SIGNALFX_TRACER', None) is not None:
            config.tracer = settings.SIGNALFX_TRACER
        if getattr(settings, 'SIGNALFX_TRACER_CALLABLE', None) is not None:
            config.tracer_callable = settings.SIGNALFX_TRACER_CALLABLE
        if getattr(settings, 'SIGNALFX_TRACER_PARAMETERS', None) is not None:
            config.tracer_parameters = settings.SIGNALFX_TRACER_PARAMETERS
        if getattr(settings, 'SIGNALFX_SET_GLOBAL_TRACER', None) is not None:
            config.set_global_tracer = settings.SIGNALFX_SET_GLOBAL_TRACER
        if getattr(settings, 'SIGNALFX_MIDDLEWARE_CLASS', None) is not None:
            config.middleware_class = settings.SIGNALFX_MIDDLEWARE_CLASS
        instrument()
