# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import os.path
import os

from django.conf import settings
import pytest

from signalfx_tracing.libraries.django_.instrument import config
from signalfx_tracing.instrumentation import uninstrument
from .app import settings as app_settings


# We should be able to invoke pytest from any project directory
root_urlconf = app_settings.ROOT_URLCONF
rel_package = os.path.dirname(os.path.relpath(__file__)).replace('/', '.')
rel_urlconf = '{}.{}'.format(rel_package, root_urlconf)
settings.configure(ROOT_URLCONF=rel_urlconf)

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.unit.libraries.django_.app.settings'


class DjangoTestSuite(object):

    @pytest.fixture(autouse=True)
    def restored_django_config(self):
        orig = dict(config.__dict__)
        yield
        config.__dict__ = orig

    @pytest.fixture(autouse=True)
    def uninstrument_django(self):
        yield
        uninstrument('django')
