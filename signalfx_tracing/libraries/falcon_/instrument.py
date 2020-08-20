# Copyright (C) 2020 SignalFx. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils

from .middleware import TraceMiddleware


config = utils.Config(
    tracer=None,
    traced_attributes=['path'],
)


def instrument(tracer=None):
    falcon = utils.get_module("falcon")
    if utils.is_instrumented(falcon):
        return

    _tracer = tracer or config.tracer or opentracing.tracer

    def traced_init(wrapped, instance, args, kwargs):
        mw = kwargs.pop("middleware", [])

        mw.insert(0, TraceMiddleware(_tracer, config.traced_attributes))
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
