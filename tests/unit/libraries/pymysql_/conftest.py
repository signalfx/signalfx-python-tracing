# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import pytest

from signalfx_tracing.libraries.pymysql_.instrument import config, uninstrument


class PyMySQLTestSuite(object):

    @pytest.fixture(autouse=True)
    def restored_pymysql_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_pymysql(self):
        yield
        uninstrument()
