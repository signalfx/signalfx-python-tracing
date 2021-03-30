# Copyright (C) 2020 SignalFx. All rights reserved.
import os
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils

from .middleware import TraceMiddleware


config = utils.Config(
    tracer=None,
    traced_attributes=['path'],
    trace_response_header=None,
)


def instrument(tracer=None):
    falcon = utils.get_module("falcon")
    if utils.is_instrumented(falcon):
        return

    _tracer = tracer or config.tracer or opentracing.tracer

    def traced_init(wrapped, instance, args, kwargs):
        mw = kwargs.pop("middleware", [])

        trace_response_header = config.trace_response_header or utils.is_truthy(
            os.environ.get('SPLUNK_CONTEXT_SERVER_TIMING_ENABLED', 'false')
        )

        mw.insert(0, TraceMiddleware(_tracer, config.traced_attributes, trace_response_header))
        kwargs["middleware"] = mw

        wrapped(*args, **kwargs)

    wrap_function_wrapper("falcon", "API.__init__", traced_init)
    utils.mark_instrumented(falcon)


def uninstrument():
    falcon = utils.get_module("falcon")
    if not utils.is_instrumented(falcon):
        return

    utils.revert_wrapper(falcon.API, "__init__")
    utils.mark_uninstrumented(falcon)
