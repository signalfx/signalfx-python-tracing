# Copyright (C) 2019 SignalFx, Inc. All rights reserved.
import logging

from wrapt import wrap_function_wrapper
from opentracing.ext import tags
import opentracing

from signalfx_tracing import utils

log = logging.getLogger(__name__)

# Configures Psycopg tracing as described by
# https://github.com/signalfx/python-dbapi/blob/master/README.rst
config = utils.Config(
    traced_commands=['execute', 'executemany', 'callproc', 'commit', 'rollback'],
    span_tags=None,
    tracer=None,
)


def instrument(tracer=None):
    psycopg2 = utils.get_module('psycopg2')
    if utils.is_instrumented(psycopg2):
        return

    dbapi_opentracing = utils.get_module('dbapi_opentracing')

    def psycopg2_tracer(connect, _, args, kwargs):
        """
        A function wrapper of psycopg2.connect() to create a corresponding
        dbapi_opentracing.ConnectionTracing upon database connection.
        """

        connection = connect(*args, **kwargs)
        _tracer = tracer or config.tracer or opentracing.tracer

        traced_commands = set(config.traced_commands)
        traced_commands_kwargs = dict(trace_execute=False, trace_executemany=False, trace_callproc=False,
                                      trace_commit=False, trace_rollback=False)
        for command in traced_commands:
            flag = 'trace_{}'.format(command.lower())
            if flag not in traced_commands_kwargs:
                log.warn('Unable to trace Psycopg command "{}".  Ignoring.'.format(command))
                continue
            traced_commands_kwargs[flag] = True

        span_tags = {tags.DATABASE_TYPE: 'PostgreSQL'}
        if config.span_tags is not None:
            span_tags.update(config.span_tags)

        return dbapi_opentracing.ConnectionTracing(connection, _tracer, span_tags=span_tags,
                                                   **traced_commands_kwargs)

    wrap_function_wrapper('psycopg2', 'connect', psycopg2_tracer)
    utils.mark_instrumented(psycopg2)


def uninstrument():
    """
    Will only prevent new Connections from registering tracers.
    It's not reasonably feasible to unwrap existing ConnectionTracing instances
    """
    psycopg2 = utils.get_module('psycopg2')
    if not utils.is_instrumented(psycopg2):
        return

    utils.revert_wrapper(psycopg2, 'connect')
    utils.mark_uninstrumented(psycopg2)
