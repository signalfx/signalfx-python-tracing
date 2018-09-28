# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import opentracing

from signalfx_tracing import utils


# Configures Django tracing as described by
# https://github.com/opentracing-contrib/python-django/blob/master/README.rst
config = utils.Config(
    trace_all=True,
    traced_attributes=['path', 'method'],
    tracer_callable='opentracing.Tracer',
    tracer_parameters={},
    tracer=None,
    set_global_tracer=False,
    middleware_class='django_opentracing.OpenTracingMiddleware',
)


def get_middleware_and_setting_name():
    """
    Returns the correct middleware list and the setting name for Django 1.10+ support:
    https://docs.djangoproject.com/en/2.1/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    """
    # Deferred, explicit imports for supporting various environments and increasing testability
    django = utils.get_module('django')
    settings = utils.get_module('django.conf').settings
    if hasattr(settings, 'MIDDLEWARE') and django.VERSION > (1, 10):
        middleware = settings.MIDDLEWARE
        if middleware is None:
            middleware = []
        return middleware, 'MIDDLEWARE'
    return settings.MIDDLEWARE_CLASSES, 'MIDDLEWARE_CLASSES'


def instrument(tracer=None):
    django = utils.get_module('django')
    if utils.is_instrumented(django):
        return

    tracer = tracer or config.tracer or opentracing.tracer

    settings = utils.get_module('django.conf').settings
    # Tracer settings (need to be before initialization)
    settings.OPENTRACING_TRACE_ALL = config.trace_all
    settings.OPENTRACING_TRACED_ATTRIBUTES = config.traced_attributes

    # Tracer initialization
    settings.OPENTRACING_SET_GLOBAL_TRACER = config.set_global_tracer
    if not config.set_global_tracer:
        django_opentracing = utils.get_module('django_opentracing')
        settings.OPENTRACING_TRACER = django_opentracing.DjangoTracer(tracer)
    else:
        settings.OPENTRACING_TRACER_CALLABLE = config.tracer_callable
        settings.OPENTRACING_TRACER_PARAMETERS = config.tracer_parameters

    middleware_classes, setting = get_middleware_and_setting_name()
    setattr(settings, setting, [config.middleware_class] + list(middleware_classes))
    utils.mark_instrumented(django)


def uninstrument():
    django = utils.get_module('django')
    if not utils.is_instrumented(django):
        return

    settings = utils.get_module('django.conf').settings
    for setting in ('OPENTRACING_TRACE_ALL', 'OPENTRACING_TRACED_ATTRIBUTES',
                    'OPENTRACING_TRACER_CALLABLE', 'OPENTRACING_TRACER_PARAMETERS',
                    'OPENTRACING_SET_GLOBAL_TRACER', 'OPENTRACING_TRACER'):
        try:
            delattr(settings, setting)
        except AttributeError:
            pass

    middleware, setting = get_middleware_and_setting_name()
    middleware_classes = [i for i in middleware if i != config.middleware_class]
    setattr(settings, setting, middleware_classes)
    utils.mark_uninstrumented(django)
