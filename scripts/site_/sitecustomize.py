# Copyright (C) 2019 SignalFx. All rights reserved.
from __future__ import print_function

import traceback
import os.path
import sys

from signalfx_tracing import auto_instrument, create_tracer
from signalfx_tracing.utils import get_module, TracerProxy


access_token = os.environ.get('SIGNALFX_ACCESS_TOKEN')


def create_celery_tracer():
    import opentracing
    tracer_proxy = TracerProxy()
    opentracing.tracer = tracer_proxy
    auto_instrument(tracer_proxy)

    from celery.signals import worker_process_init

    @worker_process_init.connect(weak=False)
    def create_global_tracer(*args, **kwargs):
        tracer = create_tracer(access_token=access_token, set_global=False)
        tracer_proxy.set_tracer(tracer)


if hasattr(sys, 'argv') and sys.argv[0].split(os.path.sep)[-1] == 'celery' and 'worker' in sys.argv:
    create_celery_tracer()
else:
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

# Attempt to load any existing sitecustomize
module = get_module('sitecustomize')
if module is None:  # reset to our own if no preexisting
    sys.modules['sitecustomize'] = sys.modules['sfx_sitecustomize']
