# Copyright (C) 2018 SignalFx. All rights reserved.

import sys
import opentracing
import logging

from signalfx_tracing import create_tracer
from signalfx_tracing.utils import trace
from signalfx_tracing.libraries.logging_.instrument import instrument, config

from .conftest import LoggingTestSuite

if sys.version_info >= (3, 0, 0):
    from io import StringIO
else:
    from cStringIO import StringIO  # noqa


class TestLogging(LoggingTestSuite):

    def setup_tracing(self, caplog):
        self.tracer = create_tracer()
        instrument(self.tracer)
        opentracing.tracer = self.tracer
        caplog.set_level(logging.INFO)

    def test_injection_disabled(self, caplog):
        config.enabled = False

        self.setup_tracing(caplog)

        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            logging.getLogger().info('log statement')
            return 123

        assert traced_function(1, one=1) == 123

        assert len(caplog.records) == 1
        assert len(caplog.messages) == 1
        assert 'sfxSpanId' not in caplog.records[0].__dict__
        assert 'sfxTraceId' not in caplog.records[0].__dict__

    def test_injection(self, caplog):
        config.enabled = True
        self.setup_tracing(caplog)

        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            logging.getLogger().info('log statement')
            return 123

        assert traced_function(1, one=1) == 123
        assert len(caplog.records) == 1
        assert len(caplog.messages) == 1
        record = caplog.records[0]

        assert 'sfxSpanId' in record.__dict__
        assert 'sfxTraceId' in record.__dict__
