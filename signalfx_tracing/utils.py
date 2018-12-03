# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import importlib
import sys
import os

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


def create_tracer(access_token=None, set_global=True, config=None, *args, **kwargs):
    """
    Creates a jaeger_client.Tracer via Config().initialize_tracer().
    Default config argument will consist of service name of 'SignalFx-Tracing' value,
    B3 span propagation, and a ConstSampler.
    """
    config = config or dict(service_name='SignalFx-Tracing')
    access_token = access_token or os.environ.get('SIGNALFX_ACCESS_TOKEN')

    if 'jaeger_endpoint' not in config:
        config['jaeger_endpoint'] = 'https://ingest.signalfx.com/v1/trace'
    if 'jaeger_user' not in config and access_token:
        config['jaeger_user'] = 'auth'
    if 'jaeger_password' not in config and access_token:
        config['jaeger_password'] = access_token
    if 'sampler' not in config:
        config['sampler'] = dict(type='const', param=1)
    if 'propagation' not in config:
        config['propagation'] = 'b3'

    from jaeger_client import Config
    jaeger_config = Config(config, *args, **kwargs)

    tracer = jaeger_config.initialize_tracer()
    if set_global:
        import opentracing
        opentracing.tracer = tracer
    return tracer
