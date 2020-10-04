# Copyright (C) 2018-2019 SignalFx. All rights reserved.
import logging
import functools
import importlib
import atexit
import sys
import os

from wrapt import decorator, ObjectProxy
import opentracing

from .constants import default_max_tag_value_length, instrumented_attr
from .tags import SFX_TRACING_LIBRARY, SFX_TRACING_VERSION
from .version import __version__


# Accepted case-insensitive disabling environment variable values
_falsy = ('0', '0.0', 'f', 'false', 'n', 'no')


# Tracer instance from create_tracer()
_tracer = None


def is_truthy(value):
    return bool(value) and str(value).lower() not in _falsy


def get_module(library):
    """Attempts import a library by name, returning None if not available"""
    if library not in sys.modules:
        try:
            importlib.import_module(library)
        except ImportError:
            return None
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


def instrumentation_disabled(library):
    env_var = _get_env_var('SIGNALFX_{}_ENABLED'.format(library.upper()), True)
    return not is_truthy(env_var)


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

    By default this function is partially memoized so that the tracer returned on first invocation
    will always be returned in subsequent calls, no matter their arguments.  It can be overridden
    if `allow_multiple` is a provided as a named argument with True value, with the resulting tracer
    being cached.
    """
    global _tracer

    allow_multiple = kwargs.pop('allow_multiple', False)
    if not allow_multiple and _tracer is not None:
        return _tracer

    try:
        from jaeger_client import Config
        from jaeger_client import constants
    except ImportError:
        raise RuntimeError('create_tracer() is only for environments with jaeger-client installed.')

    config = config or {}
    if 'service_name' not in config and 'service_name' not in kwargs:
        config['service_name'] = _get_env_var('SIGNALFX_SERVICE_NAME', 'SignalFx-Tracing')

    if 'jaeger_endpoint' not in config:
        config['jaeger_endpoint'] = _get_env_var(
            'SIGNALFX_ENDPOINT_URL',
            _get_env_var('SIGNALFX_INGEST_URL',  # Backwards compatibility
                         'http://localhost:9080/v1/trace')
        )

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

    logger = logging.getLogger('signalfx-tracing')
    config['logging'] = True
    config['logger'] = logger

    if _get_env_var('SIGNALFX_TRACING_DEBUG', False):
        logger.setLevel(logging.DEBUG)

    config['root_span_tags'] = {
        SFX_TRACING_LIBRARY: 'python-tracing',
        SFX_TRACING_VERSION: __version__
    }

    config['max_tag_value_length'] = int(_get_env_var(
        'SIGNALFX_RECORDED_VALUE_MAX_LENGTH',
        default_max_tag_value_length,
    ))

    jaeger_config = Config(config, *args, **kwargs)

    tracer = jaeger_config.new_tracer()

    atexit.register(tracer.close)

    if set_global:
        import opentracing
        opentracing.tracer = tracer

    _tracer = tracer

    return tracer


def _get_env_var(env_var, default=None):
    not_provided = '__not_provided__'
    val = os.environ.get(env_var, not_provided)
    return default if val == not_provided else val


def trace(operation_name=None, tags=None, **kwargs):
    """Tracer decorator to allow easy instrumentation:
    @trace
    def my_traced_function():  # operation name defaults to function name
        return do_work()

    @trace(operation_name='myOperationName', tags=dict(desired_tag='desired_value'))
    def my_other_traced_function(*args, **kwargs):
        # Will be active span created for this traced method
        span = opentracing.tracer.active_span
        span.log_kv(dict(some='thing'))
        span.set_tag('MyTag', 'MyValue')
        return 'MyValue'

    @trace('myOtherOperationName', dict(desired_tag='desired_value'))
    def another_traced_function(*args, **kwargs):
        span = opentracing.tracer.active_span
        span.set_tag('MyTag', 'MyValue')
        return 'MyValue'
    """

    # operation_name will be the traced function if not providing trace arguments
    if not callable(operation_name):
        deferred_kwargs = dict(tags=tags)
        if operation_name is not None:  # not only tags provided
            deferred_kwargs['deferred_operation_name'] = operation_name
        return functools.partial(trace, **deferred_kwargs)

    _wrapped = operation_name
    operation_name = kwargs.pop('deferred_operation_name', _wrapped.__name__)

    @decorator
    def _trace(wrapped, _, _args, _kwargs):
        with opentracing.tracer.start_active_span(operation_name, tags=tags):
            return wrapped(*_args, **_kwargs)

    return _trace(_wrapped)


class TracerProxy(ObjectProxy):
    """To be used in cases where auto-instrumentation requires a tracer instance before creating one is viable."""
    def __init__(self):
        super(TracerProxy, self).__init__(opentracing.tracer)

    def set_tracer(self, tracer):
        self.__wrapped__ = tracer
