# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import pytest

from signalfx_tracing.libraries.flask_.instrument import config, uninstrument


class FlaskTestSuite(object):

    @pytest.fixture(autouse=True)
    def restored_flask_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_flask(self):
        yield
        uninstrument()
