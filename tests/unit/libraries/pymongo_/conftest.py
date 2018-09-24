# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from mockupdb import MockupDB
import pytest

from signalfx_tracing.libraries.pymongo_.instrument import config, uninstrument


class PyMongoTestSuite(object):

    @pytest.fixture(autouse=True)
    def mocked_mongo(self):
        try:
            self.server = MockupDB(auto_ismaster={"maxWireVersion": 3})
            self.server.run()
            yield
        finally:
            self.server.stop()

    @pytest.fixture(autouse=True)
    def restored_pymongo_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_pymongo(self):
        yield
        uninstrument()
