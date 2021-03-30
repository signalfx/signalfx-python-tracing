# Copyright (C) 2019 SignalFx. All rights reserved.
import pytest

from signalfx_tracing.libraries.psycopg2_.instrument import config, uninstrument


class Psycopg2TestSuite(object):
    @pytest.fixture(autouse=True)
    def restored_psycopg2_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_psycopg2(self):
        yield
        uninstrument()
