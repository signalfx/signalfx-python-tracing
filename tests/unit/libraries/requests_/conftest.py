# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import pytest

from signalfx_tracing.libraries.requests_.instrument import config, uninstrument


class RequestsTestSuite(object):

    @pytest.fixture(autouse=True)
    def restored_requests_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_requests(self):
        yield
        uninstrument()
