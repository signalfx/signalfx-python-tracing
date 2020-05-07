# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
from . import patch_span  # noqa    
from .instrumentation import instrument, uninstrument, auto_instrument  # noqa
from .utils import create_tracer, trace  # noqa

__version__ = '1.0.0b1'

# Django
default_app_config = 'signalfx_tracing.libraries.django_.apps.SignalFxConfig'  # noqa
