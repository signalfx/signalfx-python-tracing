# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import logging
import pkgutil
import sys
import os

from .constants import traceable_libraries, auto_instrumentable_libraries
from .utils import is_truthy, get_module


log = logging.getLogger(__name__)


# This set of helpers operates under the assumption that a library
# is a string representation of a python package/module name
# and a module is the item in sys.modules after import, keyed by library name.

def _tracing_enabled():
    return is_truthy(os.environ.get('SIGNALFX_TRACING_ENABLED', True))


def _importable_libraries(*libraries):
    """
    Of all traceable_libraries, separate those available and unavailable
    in current execution path.
    """
    available = []
    unavailable = []
    for library in libraries:
        if library in sys.modules or pkgutil.find_loader(library) is not None:
            available.append(library)
        else:
            unavailable.append(library)
    return available, unavailable


def imported_instrumentor(library):
    """
    Convert a library name to that of the correlated auto-instrumentor
    in the libraries package.
    """
    instrumentor_lib = 'signalfx_tracing.libraries.{}_'.format(library)
    return get_module(instrumentor_lib)


def instrument(tracer=None, **libraries):
    """
    For each library/instrument_bool pair, invoke the associated
    auto-instrumentor.instrument() or uninstrument().

    If tracer isn't provided, it's up to the individual instrumentors
    to default to opentracing.tracer.  This is so individual library
    Config objects take precedence, which wouldn't happen if we used
    the global tracer by default here or in auto_instrument.
    """
    if not _tracing_enabled():
        return

    for library, inst in libraries.items():
        if library not in traceable_libraries:
            log.warn('Unable to trace {}'.format(library))
        elif not inst:
            uninstrument(library)
        else:
            imported_instrumentor(library).instrument(tracer)


def uninstrument(*libraries):
    """Invoke the associated auto-instrumentor.uninstrument() for each specified library"""
    for library in libraries:
        instrumentor = imported_instrumentor(library)
        instrumentor.uninstrument()


def auto_instrument(tracer=None):
    """
    Invoke an auto-instrumentor.instrument() for all auto_instrumentable_libraries
    in current execution path.
    """
    if not _tracing_enabled():
        return

    available, unavailable = _importable_libraries(*auto_instrumentable_libraries)
    for library in unavailable:
        log.debug('Unable to auto-instrument {} as it is unavailable.'.format(library))
    instrument(tracer, **{l: True for l in available})
