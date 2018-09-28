# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import logging

from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils


log = logging.getLogger(__name__)


# Configures PyMySQL tracing as described by
# https://github.com/signalfx/python-dbapi/blob/master/README.rst
config = utils.Config(
    traced_commands=['execute', 'executemany', 'callproc', 'commit', 'rollback'],
    span_tags=None,
    tracer=None,
)

traceable_connection_commands = set(('commit', 'rollback'))
traceable_cursor_commands = set(('execute', 'executemany', 'callproc'))


def instrument(tracer=None):
    pymysql = utils.get_module('pymysql')
    if utils.is_instrumented(pymysql):
        return

    pymysql_cursors = utils.get_module('pymysql.cursors')
    dbapi_opentracing = utils.get_module('dbapi_opentracing')

    def pymysql_tracer(connect, _, args, kwargs):
        """
        A function wrapper of pymysql.connect() to create a corresponding
        dbapi_opentracing.ConnectionTracing upon database connection.
        """

        connection = connect(*args, **kwargs)
        _tracer = tracer or config.tracer or opentracing.tracer
        tracing = dbapi_opentracing.ConnectionTracing(connection, _tracer, span_tags=config.span_tags)

        traced_commands = set(config.traced_commands)
        for command in traced_commands:
            if command not in traceable_connection_commands and command not in traceable_cursor_commands:
                log.warn('Unable to trace PyMySQL command "{}".  Ignoring.'.format(command))

        # Revert undesired traced commands by wrapping with originals
        for undesired_command in (traceable_connection_commands - traced_commands):
            wrapped = getattr(tracing.__wrapped__, undesired_command)
            wrap_function_wrapper(tracing, undesired_command, wrapped)

        for undesired_command in (traceable_cursor_commands - traced_commands):
            wrapped = getattr(pymysql_cursors.Cursor, undesired_command)
            # We must wrap our wrapper class for subsequent cursor() invocations
            wrap_function_wrapper(dbapi_opentracing.Cursor, undesired_command, wrapped)

        return tracing

    wrap_function_wrapper('pymysql', 'connect', pymysql_tracer)
    utils.mark_instrumented(pymysql)


def uninstrument():
    """
    Will only prevent new Connections from registering tracers.
    It's not reasonably feasible to unwrap existing ConnectionTracing instances
    """
    pymysql = utils.get_module('pymysql')
    if not utils.is_instrumented(pymysql):
        return

    connections = utils.get_module('pymysql.connections')
    cursors = utils.get_module('pymysql.cursors')
    utils.revert_wrapper(pymysql, 'connect')
    utils.revert_wrapper(connections.Connection, 'commit')
    utils.revert_wrapper(connections.Connection, 'rollback')
    utils.revert_wrapper(cursors.Cursor, 'execute')
    utils.revert_wrapper(cursors.Cursor, 'executemany')
    utils.revert_wrapper(cursors.Cursor, 'callproc')

    # Revert blacklist
    dbapi_opentracing = utils.get_module('dbapi_opentracing')
    utils.revert_wrapper(dbapi_opentracing.Cursor, 'execute')
    utils.revert_wrapper(dbapi_opentracing.Cursor, 'executemany')
    utils.revert_wrapper(dbapi_opentracing.Cursor, 'callproc')

    utils.mark_uninstrumented(pymysql)
