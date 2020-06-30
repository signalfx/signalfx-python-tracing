# Copyright (C) 2019 SignalFx. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


# Configures Celery tracing as described by
# https://github.com/signalfx/python-celery/blob/master/README.md
config = utils.Config(
    propagate=True,
    span_tags=None,
    tracer=None,
)


_celery_new = [None]
_celery_tracing_new = [None]


def celery_new(_, __, *args, **kwargs):
    """Monkey patch Celery.__new__() to create a CeleryTracing object"""
    from celery_opentracing import CeleryTracing
    return CeleryTracing.__new__(CeleryTracing, *args, **kwargs)


def celery_tracing_new(_, __, *args, **kwargs):
    """Monkey patch a valid CeleryTracing.__new__() to avoid recursion on patched base class"""
    from celery_opentracing import CeleryTracing
    return object.__new__(CeleryTracing)


def instrument(tracer=None):
    """
    Requests auto-instrumentation works by hooking a __new__ proxy for a CeleryTracing
    instance upon celery.Celery initialization to trigger proper inheritance.
    CeleryTracing.__init__ is also wrapped for correct argument injection.
    """

    celery = utils.get_module('celery')
    if utils.is_instrumented(celery):
        return

    import celery.app

    def celery_tracing_init(__init__, instance, args, kwargs):
        _tracer = tracer or config.tracer or opentracing.tracer
        __init__(*args, tracer=_tracer, propagate=config.propagate, span_tags=config.span_tags or {}, **kwargs)

    from celery_opentracing import CeleryTracing

    _celery_new[0] = celery.Celery.__new__
    _celery_tracing_new[0] = CeleryTracing.__new__

    CeleryTracing.__new__ = celery_tracing_new.__get__(CeleryTracing)
    celery.app.base.Celery.__new__ = celery_new.__get__(celery.Celery)
    wrap_function_wrapper('celery_opentracing.tracing', 'CeleryTracing.__init__', celery_tracing_init)

    utils.mark_instrumented(celery)


def uninstrument():
    celery = utils.get_module('celery')
    if not utils.is_instrumented(celery):
        return

    import celery.app

    from celery_opentracing import CeleryTracing

    if _celery_tracing_new[0] is not None:
        if hasattr(_celery_tracing_new[0], '__get__'):
            CeleryTracing.__new__ = _celery_tracing_new[0].__get__(CeleryTracing)
        else:  # builtin doesn't follow descriptor protocol
            CeleryTracing.__new__ = _celery_tracing_new[0]
    if _celery_new[0] is not None:
        if hasattr(_celery_new[0], '__get__'):
            celery.app.base.Celery.__new__ = _celery_new[0].__get__(celery.Celery)
        else:
            celery.app.base.Celery.__new__ = _celery_new[0]

    utils.revert_wrapper(CeleryTracing, '__init__')
    utils.mark_uninstrumented(celery)
