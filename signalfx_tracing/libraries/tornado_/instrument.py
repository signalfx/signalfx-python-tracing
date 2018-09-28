# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


# Configures Tornado tracing as described by
# https://github.com/opentracing-contrib/python-tornado/blob/master/README.rst
config = utils.Config(
    trace_all=True,
    trace_client=True,
    traced_attributes=['path', 'method'],
    start_span_cb=None,
    tracer=None,
)


def instrument(tracer=None):
    tornado = utils.get_module('tornado')
    if utils.is_instrumented(tornado):
        return

    tornado_opentracing = utils.get_module('tornado_opentracing')

    def _tracer_config(wrapped_tracer_config, _, wrapt_args, __):
        """
        A function wrapper for tornado_opentracing's monkey patcher of tornado.web.Application.__init__()
        used to inject tracer configuration as settings arguments.  As a wrapt function wrapper of a
        function_wrapper, _tracer_config's meaningful arguments are oddly nested.
        """
        __init__ = wrapt_args[0]
        app = wrapt_args[1]
        args = wrapt_args[2]
        kwargs = wrapt_args[3]

        _tracer = tracer or config.tracer or opentracing.tracer
        kwargs['opentracing_tracing'] = tornado_opentracing.TornadoTracing(_tracer)
        kwargs['opentracing_trace_all'] = config.trace_all
        kwargs['opentracing_trace_client'] = config.trace_client
        kwargs['opentracing_traced_attributes'] = config.traced_attributes
        kwargs['opentracing_start_span_cb'] = config.start_span_cb

        wrapped_tracer_config(__init__, app, args, kwargs)

    wrap_function_wrapper('tornado_opentracing.application', 'tracer_config', _tracer_config)
    tornado_opentracing.init_tracing()
    utils.mark_instrumented(tornado)


def uninstrument():
    tornado = utils.get_module('tornado')
    if not utils.is_instrumented(tornado):
        return

    tornado_initialization = utils.get_module('tornado_opentracing.initialization')
    tornado_initialization._unpatch_tornado()
    tornado_initialization._unpatch_tornado_client()

    utils.mark_uninstrumented(tornado)
