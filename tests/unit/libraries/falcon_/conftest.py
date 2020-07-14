# Copyright (C) 2018 SignalFx. All rights reserved.
import pytest

from signalfx_tracing.libraries.falcon_.instrument import config, uninstrument


class FalconTestSuite(object):
    @pytest.fixture(autouse=True)
    def restored_falcon_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_falcon(self):
        yield
        uninstrument()
