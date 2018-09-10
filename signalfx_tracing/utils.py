# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import importlib
import sys

from wrapt import ObjectProxy

from .constants import instrumented_attr


def get_module(library):
    if library not in sys.modules:
        importlib.import_module(library)
    return sys.modules[library]


def is_instrumented(module):
    return bool(getattr(module, instrumented_attr, False))


def mark_instrumented(module):
    setattr(module, instrumented_attr, True)


def mark_uninstrumented(module):
    try:
        delattr(module, instrumented_attr)
    except AttributeError:
        pass


class Config(object):
    """A basic namespace"""

    def __init__(self, **core):
        self.__dict__.update(core)

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, item, value):
        self.__dict__[item] = value


def revert_wrapper(obj, wrapped_attr):
    """Reverts a wrapt.wrap_function_wrapper() invocation"""
    attr = getattr(obj, wrapped_attr, None)
    if attr is not None and isinstance(attr, ObjectProxy) and hasattr(attr, '__wrapped__'):
        setattr(obj, wrapped_attr, attr.__wrapped__)
