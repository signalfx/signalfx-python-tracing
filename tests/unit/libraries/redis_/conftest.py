# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import pytest

from signalfx_tracing.libraries.redis_.instrument import config, uninstrument


class RedisTestSuite(object):

    @pytest.fixture(autouse=True)
    def restored_redis_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_redis(self):
        yield
        uninstrument()
