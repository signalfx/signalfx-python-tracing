# Copyright (C) 2019 SignalFx, Inc. All rights reserved.
from __future__ import print_function

import traceback
import os.path
import sys

from signalfx_tracing import auto_instrument, create_tracer
from signalfx_tracing.utils import get_module


access_token = os.environ.get('SIGNALFX_ACCESS_TOKEN')

try:
    auto_instrument(create_tracer(access_token=access_token, set_global=True))
except Exception:
    print(traceback.format_exc())

# Do not prevent existing sitecustomize module import. Done by
# removing this module's package and attempting to import
# sitecustomize module.

# Removing references to this sitecustomize module
# can trigger garbage collection and cause lookup failures in other modules.
sys.modules['sfx_sitecustomize'] = sys.modules.pop('sitecustomize', None)
sys.path.remove(os.path.abspath(os.path.dirname(__file__)))
try:
    get_module('sitecustomize')
except ImportError:
    pass
