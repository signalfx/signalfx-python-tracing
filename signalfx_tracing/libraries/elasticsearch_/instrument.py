# Copyright (C) 2019 SignalFx, Inc. All rights reserved.
import opentracing

from signalfx_tracing import utils

# Configures Elasticsearch tracing as described by
# https://github.com/opentracing-contrib/python-elasticsearch/blob/master/README.rst
config = utils.Config(
    prefix='Elasticsearch',
    tracer=None,
)

_transport_new = [None]
_tracing_transport_new = [None]


def transport_new(_, __, *args, **kwargs):
    """Monkey patch Transport.__new__() to create a TracingTransport object"""
    from elasticsearch_opentracing import TracingTransport
    return TracingTransport.__new__(TracingTransport, *args, **kwargs)


def tracing_transport_new(_, __, *args, **kwargs):
    """Monkey patch a valid TracingTransport.__new__() to avoid recursion on patched base class"""
    from elasticsearch_opentracing import TracingTransport
    return object.__new__(TracingTransport)


def instrument(tracer=None):
    """
    Elasticsearch auto-instrumentation works by hooking a __new__ proxy for a TracingTransport
    instance upon elasticsearch.transports.Transport initialization to trigger proper inheritance.
    """
    elasticsearch = utils.get_module('elasticsearch')
    if utils.is_instrumented(elasticsearch):
        return

    from elasticsearch_opentracing import init_tracing, TracingTransport

    _tracer = tracer or config.tracer or opentracing.tracer
    init_tracing(_tracer, trace_all_requests=True, prefix=config.prefix)

    _transport_new[0] = elasticsearch.transport.Transport.__new__
    _tracing_transport_new[0] = TracingTransport.__new__

    TracingTransport.__new__ = tracing_transport_new.__get__(TracingTransport)
    elasticsearch.transport.Transport.__new__ = transport_new.__get__(elasticsearch.transport.Transport)

    utils.mark_instrumented(elasticsearch)


def uninstrument():
    elasticsearch = utils.get_module('elasticsearch')
    if not utils.is_instrumented(elasticsearch):
        return

    from elasticsearch_opentracing import disable_tracing, TracingTransport
    disable_tracing()

    # because of https://bugs.python.org/issue25731 we cannot simply restore
    # built-in __new__.  Use a generic implementation as a workaround
    def __new__(cls, *_, **__):
        return object.__new__(cls)

    if _tracing_transport_new[0] is not None:
        if hasattr(_tracing_transport_new[0], '__get__'):
            TracingTransport.__new__ = _tracing_transport_new[0].__get__(TracingTransport)
        else:  # builtin doesn't follow descriptor protocol
            TracingTransport.__new__ = __new__.__get__(TracingTransport)
        _tracing_transport_new[0] = None

    if _transport_new[0] is not None:
        if hasattr(_transport_new[0], '__get__'):
            elasticsearch.transport.Transport.__new__ = _transport_new[0].__get__(elasticsearch.transport.Transport)
        else:
            elasticsearch.transport.Transport.__new__ = __new__.__get__(elasticsearch.transport.Transport)
        _transport_new[0] = None
    utils.mark_uninstrumented(elasticsearch)
