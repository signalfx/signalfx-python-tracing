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
    B3 span propagation, and a ConstSampler.  These are tunable by env vars.
    """
    try:
        from jaeger_client import Config
        from jaeger_client import constants
    except ImportError:
        raise RuntimeError('create_tracer() is only for environments with jaeger-client installed.')

    config = config or {}
    if 'service_name' not in config:
        config['service_name'] = _get_env_var('SIGNALFX_SERVICE_NAME', 'SignalFx-Tracing')

    if 'jaeger_endpoint' not in config:
        config['jaeger_endpoint'] = _get_env_var('SIGNALFX_INGEST_URL', 'https://ingest.signalfx.com/v1/trace')

    access_token = access_token or _get_env_var('SIGNALFX_ACCESS_TOKEN')
    if 'jaeger_user' not in config and access_token is not None:
        config['jaeger_user'] = 'auth'
    if 'jaeger_password' not in config and access_token is not None:
        config['jaeger_password'] = access_token

    if 'sampler' not in config:
        sampler_type = _get_env_var('SIGNALFX_SAMPLER_TYPE', 'const')

        sampler_param = _get_env_var('SIGNALFX_SAMPLER_PARAM', 1)
        if sampler_type == constants.SAMPLER_TYPE_CONST:
            sampler_param = int(float(sampler_param))
        elif sampler_type in (constants.SAMPLER_TYPE_PROBABILISTIC,
                              constants.SAMPLER_TYPE_RATE_LIMITING,
                              constants.SAMPLER_TYPE_LOWER_BOUND):
            sampler_param = float(sampler_param)
        config['sampler'] = dict(type=sampler_type, param=sampler_param)
    if 'propagation' not in config:
        propagation = _get_env_var('SIGNALFX_PROPAGATION', 'b3')
        config['propagation'] = propagation

    jaeger_config = Config(config, *args, **kwargs)

    tracer = jaeger_config.initialize_tracer()
    if set_global:
        import opentracing
        opentracing.tracer = tracer
    return tracer


def _get_env_var(env_var, default=None):
    not_provided = '__not_provided__'
    val = os.environ.get(env_var, not_provided)
    return default if val == not_provided else val
