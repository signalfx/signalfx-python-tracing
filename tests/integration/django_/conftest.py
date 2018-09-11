# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import os.path
import os

from django.conf import settings

from .app import settings as app_settings


# We should be able to invoke pytest from any project directory
root_urlconf = app_settings.ROOT_URLCONF
rel_package = os.path.dirname(os.path.relpath(__file__)).replace('/', '.')
rel_urlconf = '{}.{}'.format(rel_package, root_urlconf)

installed_apps = app_settings.INSTALLED_APPS
set_global_tracer = app_settings.SIGNALFX_SET_GLOBAL_TRACER
tracer_callable = app_settings.SIGNALFX_TRACER_CALLABLE
settings.configure(ROOT_URLCONF=rel_urlconf, INSTALLED_APPS=installed_apps,
                   SIGNALFX_SET_GLOBAL_TRACER=set_global_tracer,
                   SIGNALFX_TRACER_CALLABLE=tracer_callable)

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests_e2e.django_.app.settings'
