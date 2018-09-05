# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import logging
import pkgutil

import opentracing

from .constants import traceable_libraries
from .utils import get_module


log = logging.getLogger(__name__)


def _get_tracer(tracer=None):
    """Retrieve the opentracing global tracer if no tracer provided"""
    if tracer is None:
        tracer = opentracing.tracer
    return tracer

# This set of helpers operates under the assumption that a library
# is a string representation of a python package/module name
# and a module is the item in sys.modules after import, keyed by library name.


def _importable_libraries(*libraries):
    """
    Of all traceable_libraries, separate those available and unavailable
    in current execution path.
    """
    available = []
    unavailable = []
    for library in libraries:
        if pkgutil.find_loader(library) is not None:
            available.append(library)
        else:
            unavailable.append(library)
    return available, unavailable


def imported_instrumenter(library):
    """
    Convert a library name to that of the correlated auto-instrumenter
    in the libraries package.
    """
    instrumenter_lib = 'signalfx_tracing.libraries.{}_'.format(library)
    return get_module(instrumenter_lib)


def instrument(tracer=None, **libraries):
    """
    For each library/instrument_bool pair, invoke the associated
    auto-instrumenter.instrument() or uninstrument()
    """
    tracer = _get_tracer(tracer)
    for library, inst in libraries.items():
        if not inst:
            uninstrument(library)
        else:
            imported_instrumenter(library).instrument(tracer)


def uninstrument(*libraries):
    """Invoke the associated auto-instrumenter.uninstrument() for each specified library"""
    for library in libraries:
        instrumenter = imported_instrumenter(library)
        instrumenter.uninstrument()


def auto_instrument(tracer=None):
    """
    Invoke an auto-instrumenter.instrument() for all traceable_libraries
    in current execution path.
    """
    tracer = _get_tracer(tracer)
    available, unavailable = _importable_libraries(*traceable_libraries)
    for library in unavailable:
        log.debug('Unable to auto-instrument {} as it is unavailable.'.format(library))
    instrument(tracer, **{l: True for l in available})
