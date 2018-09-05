# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from .instrumentation import instrument, uninstrument, auto_instrument  # noqa

# Django
default_app_config = 'signalfx_tracing.libraries.django_.apps.SignalFxConfig'  # noqa
