# Copyright (C) 2018 SignalFx. All rights reserved.

import os
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils
from signalfx_tracing.constants import logging_format


config = utils.Config(
    injection_enabled=utils.is_truthy(os.environ.get('SIGNALFX_LOGS_INJECTION', False)),
    logging_format=os.environ.get('SIGNALFX_LOGGING_FORMAT', logging_format)
)


def padded_hex(num):
    return '{:016x}'.format(num)


def makeRecordPatched(makeRecord, instance, args, kwargs):
    rv = makeRecord(*args, **kwargs)
    span_id = ''
    trace_id = ''
    span = opentracing.tracer.active_span
    if span is not None:
        span_id = padded_hex(span.span_id)
        trace_id = padded_hex(span.trace_id)
    setattr(rv, 'sfxTraceId', span_id)
    setattr(rv, 'sfxSpanId', trace_id)
    return rv


def instrument(tracer=None):
    """
    Unlike all other instrumentations, this instrumentation does not patch the logging
    lib to automatically generate spans. Instead it patches the lib to automatically
    inject trace context into logs.
    """
    logging = utils.get_module('logging')
    if utils.is_instrumented(logging):
        return

    wrap_function_wrapper(logging, 'Logger.makeRecord', makeRecordPatched)

    if config.injection_enabled:
        level = logging.INFO
        if utils.is_truthy(os.environ.get('SIGNALFX_TRACING_DEBUG', False)):
            level = logging.DEBUG
        logging.basicConfig(level=level, format=config.logging_format)

    utils.mark_instrumented(logging)


def uninstrument():
    logging = utils.get_module('logging')
    if not utils.is_instrumented(logging):
        return

    utils.revert_wrapper(logging, 'Logger.makeRecord')
    utils.mark_uninstrumented(logging)
