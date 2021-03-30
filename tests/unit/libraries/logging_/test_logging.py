# Copyright (C) 2018 SignalFx. All rights reserved.

import sys
import opentracing
import logging

from signalfx_tracing import create_tracer
from signalfx_tracing.utils import trace
from signalfx_tracing.tags import SFX_ENVIRONMENT
from signalfx_tracing.libraries.logging_.instrument import instrument, config

from .conftest import LoggingTestSuite

if sys.version_info >= (3, 0, 0):
    from io import StringIO
else:
    from cStringIO import StringIO  # noqa


class TestLogging(LoggingTestSuite):
    def setup_tracing(self, caplog):
        tags = {SFX_ENVIRONMENT: "test"}
        self.tracer = create_tracer(config={"service_name": "loginject", "tags": tags})
        instrument(self.tracer)
        opentracing.tracer = self.tracer
        caplog.set_level(logging.INFO)

    def test_injection_disabled(self, caplog):
        config.injection_enabled = False

        self.setup_tracing(caplog)

        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            logging.getLogger().info("log statement")
            return 123

        assert traced_function(1, one=1) == 123

        assert len(caplog.records) == 1
        assert len(caplog.messages) == 1

        fields = caplog.records[0].__dict__

        assert "sfxSpanId" not in fields
        assert "sfxTraceId" not in fields
        assert "sfxService" not in fields
        assert "sfxEnvironment" not in fields

    def test_injection(self, caplog):
        config.injection_enabled = True
        self.setup_tracing(caplog)

        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            trace_id = opentracing.tracer.active_span.trace_id
            span_id = opentracing.tracer.active_span.span_id
            logging.getLogger().info("log statement")
            return trace_id, span_id

        trace_id, span_id = traced_function(1, one=1)

        assert len(caplog.records) == 1
        assert len(caplog.messages) == 1
        fields = caplog.records[0].__dict__

        assert fields.get("sfxSpanId") == "{:016x}".format(span_id)
        assert fields.get("sfxTraceId") == "{:016x}".format(trace_id)
        assert fields.get("sfxService") == "loginject"
        assert fields.get("sfxEnvironment") == "test"
