# Django

- [opentracing-contrib/python-django](https://github.com/opentracing-contrib/python-django)
- [Official Site](https://www.djangoproject.com)

The SignalFx Auto-instrumenter configures the OpenTracing Project's Django instrumentation for your Django 1.x or
2.x project.  You can enable instrumentation within your project by adding the `signalfx_tracing` instrumenter
app to your installed apps.  To configure Django tracing, some settings are provided to establish
the desired tracer and request attributes for span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| SIGNALFX\_TRACE\_ALL | Whether to trace all requests. | `True` |
| SIGNALFX\_TRACED\_ATTRIBUTES | Request attributes to use as span tags. | `['path', 'method']` |
| SIGNALFX\_TRACER | An instance of an OpenTracing-compatible tracer for all Django traces. | `opentracing.tracer` |
| SIGNALFX\_SET\_GLOBAL\_TRACER | Whether to instantiate and set opentracing.tracer with designated callable. | `False` |
| SIGNALFX\_TRACER\_CALLABLE | The Python path for the OpenTracing-compatible tracer class. | `'opentracing.Tracer'` |
| SIGNALFX\_TRACER\_PARAMETERS | A dictionary of named arguments for initializing the SIGNALFX\_TRACER\_CALLABLE. | `{}` |
| SIGNALFX\_MIDDLEWARE\_CLASS | The Django middleware configured during setup.  | `'django_opentracing.OpenTracingMiddleware'` |

```python
# my_app.settings.py
INSTALLED_APPS = [..., 'signalfx_tracing', ...]  # Enables tracing in your application

SIGNALFX_TRACE_ALL = True  # If False, will only trace those manually decorated with
# @tracer.trace('my_attr', 'another_attr'):
# https://github.com/opentracing-contrib/python-django#tracing-individual-requests

SIGNALFX_TRACED_ATTRIBUTES = ['my_attr', 'another_attr']  # Ignored if SIGNALFX_TRACE_ALL is False.

SIGNALFX_SET_GLOBAL_TRACER = True
# Equivalent to opentracing.tracer = import_module(SIGNALFX_TRACER_CALLABLE)(**SIGNALFX_TRACER_PARAMETERS)
SIGNALFX_TRACER_CALLABLE = 'my_opentracing_compatible_tracer.Tracer'
SIGNALFX_TRACER_PARAMETERS = dict(my_tracer_parameter='arg_one', another_parameter='arg_two')
# ***
# If using the Jaeger Python client, there is an known issue with
# Tracer initialization before forking: 
# https://github.com/jaegertracing/jaeger-client-python/issues/60
#
# As a workaround in Django, this pattern is suggested:
#
# from jaeger_client import Config
#
# def create_tracer():
#     config = Config(...)
#     return config.initialize_tracer()
#
# SIGNALFX_TRACER_CALLABLE = 'my_app.settings.create_tracer'
#
# Please note that you must use a version of django_opentracing
# that supports lazy tracer initialization, such as that found at
# https://github.com/rmfitzpatrick/python-django/tree/django_2_ot_2_jaeger
# ***

SIGNALFX_TRACER = MyTracer()  # Ignored if bool(SIGNALFX_SET_GLOBAL_TRACER).
# Please note that instantiating your tracer within your settings.py file can be problematic
# for some tracers (e.g. https://github.com/jaegertracing/jaeger-client-python#wsgi).
# If this is the case, using deferred initialization via SIGNALFX_SET_GLOBAL_TRACER or
# setting to opentracing.tracer with global initialization occurring in a custom configuration
# view is recommended.

SIGNALFX_MIDDLEWARE_CLASS = 'my_custom_project.MyTracingMiddleware'
```
