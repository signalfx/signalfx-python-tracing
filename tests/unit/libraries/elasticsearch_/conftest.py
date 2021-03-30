# Copyright (C) 2019 SignalFx. All rights reserved.
import unittest

import pytest

from signalfx_tracing.libraries.elasticsearch_.instrument import config, uninstrument


class ElasticsearchTestSuite(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def restored_elasticsearch_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_elasticsearch(self):
        yield
        uninstrument()
