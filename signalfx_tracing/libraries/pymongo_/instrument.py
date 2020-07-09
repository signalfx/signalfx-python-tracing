# Copyright (C) 2018 SignalFx. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


# Configures PyMongo tracing as described by
# https://github.com/signalfx/python-pymongo/blob/master/README.rst
config = utils.Config(
    span_tags=None,
    tracer=None,
)


def instrument(tracer=None):
    pymongo = utils.get_module('pymongo')
    if utils.is_instrumented(pymongo):
        return

    pymongo_opentracing = utils.get_module('pymongo_opentracing')

    def pymongo_tracer(__init__, app, args, kwargs):
        """
        A function wrapper of pymongo.MongoClient.__init__ to register a corresponding
        pymongo_opentracing.CommandTracing upon client instantiation.
        """
        _tracer = tracer or config.tracer or opentracing.tracer

        command_tracing = pymongo_opentracing.CommandTracing(
            tracer=_tracer, span_tags=config.span_tags or {},
        )

        event_listeners = list(kwargs.pop('event_listeners', []))
        event_listeners.insert(0, command_tracing)
        kwargs['event_listeners'] = event_listeners
        __init__(*args, **kwargs)

    wrap_function_wrapper('pymongo', 'MongoClient.__init__', pymongo_tracer)
    utils.mark_instrumented(pymongo)


def uninstrument():
    """
    Will only prevent new clients from registering tracers.
    It's not reasonably feasible to remove existing before/after_request
    trace methods of existing clients.
    """
    pymongo = utils.get_module('pymongo')
    if not utils.is_instrumented(pymongo):
        return

    utils.revert_wrapper(pymongo.MongoClient, '__init__')
    utils.mark_uninstrumented(pymongo)
