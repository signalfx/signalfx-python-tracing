# Copyright (C) 2019 SignalFx. All rights reserved.
import pytest

from signalfx_tracing.libraries.celery_.instrument import config, uninstrument


class CeleryTestSuite(object):
    @pytest.fixture(autouse=True)
    def restored_celery_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_celery(self):
        yield
        uninstrument()

    @pytest.fixture(autouse=True)
    def reset_signals(self):
        yield
        from celery import signals

        signals.before_task_publish.receivers = []
        signals.after_task_publish.receivers = []
