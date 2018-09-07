# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import pytest

from signalfx_tracing.libraries.tornado_.instrument import config, uninstrument


class TornadoTestSuite(object):

    @pytest.fixture(autouse=True)
    def restored_tornado_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_tornado(self):
        yield
        uninstrument()
