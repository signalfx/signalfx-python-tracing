# Copyright (C) 2018 SignalFx. All rights reserved.
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


# Configures Flask tracing as described by
# https://github.com/opentracing-contrib/python-flask/blob/master/README.rst
config = utils.Config(
    trace_all=True,
    traced_attributes=['path', 'method'],
    tracer=None,
)


def instrument(tracer=None):
    flask = utils.get_module('flask')
    if utils.is_instrumented(flask):
        return

    flask_opentracing = utils.get_module('flask_opentracing')

    def flask_tracer(__init__, app, args, kwargs):
        """
        A function wrapper of flask.Flask.__init__ to create a corresponding
        flask_opentracing.FlaskTracer upon app instantiation.
        """

        __init__(*args, **kwargs)

        _tracer = tracer or config.tracer or opentracing.tracer

        app.config['FLASK_TRACER'] = flask_opentracing.FlaskTracer(
            tracer=_tracer, trace_all_requests=config.trace_all,
            app=app, traced_attributes=config.traced_attributes
        )

    wrap_function_wrapper('flask', 'Flask.__init__', flask_tracer)
    utils.mark_instrumented(flask)


def uninstrument():
    """
    Will only prevent new applications from registering tracers.
    It's not reasonably feasible to remove existing before/after_request
    trace methods of existing apps.
    """
    flask = utils.get_module('flask')
    if not utils.is_instrumented(flask):
        return

    utils.revert_wrapper(flask.Flask, '__init__')
    utils.mark_uninstrumented(flask)
