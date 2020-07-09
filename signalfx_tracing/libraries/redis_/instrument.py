# Copyright (C) 2018 SignalFx. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


# Configures Redis tracing as described by
# https://github.com/opentracing-contrib/python-redis/blob/master/README.rst
config = utils.Config(
    tracer=None,
)


def instrument(tracer=None):
    redis = utils.get_module('redis')
    if utils.is_instrumented(redis):
        return

    redis_opentracing = utils.get_module('redis_opentracing')
    redis_opentracing.init_tracing(tracer=tracer or config.tracer or opentracing.tracer,
                                   trace_all_classes=False)

    def traced_client(__init__, client, args, kwargs):
        __init__(*args, **kwargs)
        redis_opentracing.trace_client(client)

    wrap_function_wrapper('redis.client', 'StrictRedis.__init__', traced_client)
    utils.mark_instrumented(redis)


def uninstrument():
    """Will only prevent new clients from registering tracers."""
    redis = utils.get_module('redis')
    if not utils.is_instrumented(redis):
        return

    from redis.client import StrictRedis
    utils.revert_wrapper(StrictRedis, '__init__')
    utils.mark_uninstrumented(redis)
