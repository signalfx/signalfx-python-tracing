# Copyright (C) 2019 SignalFx. All rights reserved.
from opentracing.mocktracer import MockTracer
from celery_opentracing import CeleryTracing
from celery import signals
import celery
import pytest

from signalfx_tracing.libraries.celery_ import config, instrument
from .conftest import CeleryTestSuite


class DummyAMQP(object):

    pass


class TestCeleryConfig(CeleryTestSuite):
    @pytest.mark.parametrize("propagate", (True, False))
    def test_instrument_celery_values_set_by_config(self, propagate):
        tracer = MockTracer()
        config.tracer = tracer
        config.propagate = propagate
        config.span_tags = dict(one=1, two=2)

        instrument()

        app = celery.Celery("MyCeleryApplication", amqp=DummyAMQP)

        assert isinstance(app, CeleryTracing)
        assert app._tracer is tracer
        assert app._span_tags == dict(one=1, two=2)
        assert app.main == "MyCeleryApplication"
        assert app.amqp_cls == DummyAMQP

        if propagate:
            assert signals.before_task_publish.receivers
            assert signals.after_task_publish.receivers
        else:
            assert not signals.before_task_publish.receivers
            assert not signals.before_task_publish.receivers
