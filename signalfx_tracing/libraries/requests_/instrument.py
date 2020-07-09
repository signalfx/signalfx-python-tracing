# Copyright (C) 2018 SignalFx. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


# Configures Requests tracing as described by
# https://github.com/signalfx/python-requests/blob/master/README.rst
config = utils.Config(
    propagate=True,
    span_tags=None,
    tracer=None,
)


_session_new = [None]
_session_tracing_new = [None]


def session_new(_, __, *args, **kwargs):
    """Monkey patch Session.__new__() to create a SessionTracing object"""
    from requests_opentracing import SessionTracing
    return SessionTracing.__new__(SessionTracing)


def session_tracing_new(_, __, *args, **kwargs):
    """Monkey patch a valid SessionTracing.__new__() to avoid recursion on patched base class"""
    from requests_opentracing import SessionTracing
    return object.__new__(SessionTracing)


def instrument(tracer=None):
    """
    Requests auto-instrumentation works by hooking a __new__ proxy for a SessionTracing
    instance upon requests.sessions.Session initialization to trigger proper inheritance.
    SessionTracing.__init__ is also wrapped for correct argument injection.
    """

    requests = utils.get_module('requests')
    if utils.is_instrumented(requests):
        return

    def session_tracing_init(__init__, instance, _, __):
        _tracer = tracer or config.tracer or opentracing.tracer
        __init__(_tracer, propagate=config.propagate, span_tags=config.span_tags or {})

    from requests_opentracing import SessionTracing

    _session_new[0] = requests.Session.__new__
    _session_tracing_new[0] = SessionTracing.__new__

    SessionTracing.__new__ = session_tracing_new.__get__(SessionTracing)
    requests.Session.__new__ = session_new.__get__(requests.Session)
    wrap_function_wrapper('requests_opentracing.tracing', 'SessionTracing.__init__', session_tracing_init)

    utils.mark_instrumented(requests)


def uninstrument():
    requests = utils.get_module('requests')
    if not utils.is_instrumented(requests):
        return

    from requests_opentracing import SessionTracing

    if _session_tracing_new[0] is not None:
        if hasattr(_session_tracing_new[0], '__get__'):
            SessionTracing.__new__ = _session_tracing_new[0].__get__(SessionTracing)
        else:  # builtin doesn't follow descriptor protocol
            SessionTracing.__new__ = _session_tracing_new[0]
    if _session_new[0] is not None:
        if hasattr(_session_new[0], '__get__'):
            requests.Session.__new__ = _session_new[0].__get__(requests.Session)
        else:
            requests.Session.__new__ = _session_new[0]

    utils.revert_wrapper(SessionTracing, '__init__')
    utils.mark_uninstrumented(requests)
