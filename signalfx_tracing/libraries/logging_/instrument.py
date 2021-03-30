# Copyright (C) 2018 SignalFx. All rights reserved.

import os
from wrapt import wrap_function_wrapper
import opentracing

from signalfx_tracing import utils, tags
from signalfx_tracing.constants import logging_format
from signalfx_tracing.utils import padded_hex

config = utils.Config(
    injection_enabled=utils.is_truthy(os.environ.get("SIGNALFX_LOGS_INJECTION", False)),
    logging_format=os.environ.get("SIGNALFX_LOGGING_FORMAT", logging_format),
)


def makeRecordPatched(tracer):
    def patched(makeRecord, instance, args, kwargs):
        rv = makeRecord(*args, **kwargs)

        fields = {
            "sfxTraceId": "",
            "sfxSpanId": "",
            "sfxService": "",
            "sfxEnvironment": "",
        }

        span = tracer.active_span

        if span is not None:
            fields["sfxTraceId"] = padded_hex(span.trace_id)
            fields["sfxSpanId"] = padded_hex(span.span_id)
            fields["sfxService"] = tracer.service_name
            fields["sfxEnvironment"] = tracer.tags.get(tags.SFX_ENVIRONMENT, "")

        for field in fields:
            setattr(rv, field, fields[field])

        return rv

    return patched


def instrument(tracer=None):
    """
    Unlike all other instrumentations, this instrumentation does not patch the logging
    lib to automatically generate spans. Instead it patches the lib to automatically
    inject trace context into logs.
    """
    logging = utils.get_module("logging")

    if utils.is_instrumented(logging):
        return

    if not config.injection_enabled:
        return

    tracer = tracer or opentracing.tracer
    wrap_function_wrapper(logging, "Logger.makeRecord", makeRecordPatched(tracer))
    level = logging.INFO

    if utils.is_truthy(os.environ.get("SIGNALFX_TRACING_DEBUG", False)):
        level = logging.DEBUG

    logging.basicConfig(level=level, format=config.logging_format)

    utils.mark_instrumented(logging)


def uninstrument():
    logging = utils.get_module("logging")
    if not utils.is_instrumented(logging):
        return

    utils.revert_wrapper(logging.Logger, "makeRecord")
    utils.mark_uninstrumented(logging)
