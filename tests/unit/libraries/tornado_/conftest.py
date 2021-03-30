# Copyright (C) 2018 SignalFx. All rights reserved.
import pytest

from tornado.testing import AsyncHTTPTestCase as BaseAsyncHTTPTestCase

from signalfx_tracing.libraries.tornado_.instrument import config, uninstrument


class AsyncHTTPTestCase(BaseAsyncHTTPTestCase):
    def http_fetch(self, url, *args, **kwargs):
        self.http_client.fetch(url, self.stop, *args, **kwargs)
        return self.wait()


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
