# Django

- [opentracing-contrib/python-django](https://github.com/opentracing-contrib/python-django)
- [Official Site](https://www.djangoproject.com)

The SignalFx Auto-instrumentor configures the OpenTracing Project's Django instrumentation for your Django 1.x or
2.x project.  You can enable instrumentation within your project by adding the `signalfx_tracing` instrumentor
app to your installed apps and specifying your tracer callable:

```python
# settings.py
INSTALLED_APPS = ['signalfx_tracing']
```

Your Django app will then be able to report spans to SignalFx:

```bash
 $ SIGNALFX_INGEST_URL='http://MySmartAgentOrGateway:9080/v1/trace' \
   SIGNALFX_SERVICE_NAME='MyApp' sfx-py-trace manage.py runserver 0.0.0.0:8001
```

To configure Django tracing, some settings are provided to establish
the desired tracer and request attributes for span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| SIGNALFX\_TRACE\_ALL | Whether to trace all requests. | `True` |
| SIGNALFX\_TRACED\_ATTRIBUTES | Request attributes to use as span tags. | `['path', 'method']` |
| SIGNALFX\_TRACER\_CALLABLE | The Python path for an OpenTracing-compatible tracer class or callable that returns an instance. | `None` |
| SIGNALFX\_TRACER\_PARAMETERS | A dictionary of named arguments for initializing the SIGNALFX\_TRACER\_CALLABLE. | `{}` |
| SIGNALFX\_TRACER | An instance of an OpenTracing-compatible tracer for all Django traces. | `opentracing.tracer` if no callable provided |
| SIGNALFX\_SET\_GLOBAL\_TRACER | Whether to set global opentracing.tracer from this instrumentation's DjangoTracing().tracer (not recommended). | `False` |
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

SIGNALFX_TRACER = MyTracer()  # Ignored if SIGNALFX_TRACER_CALLABLE is not None
# ******************************************************************
# Please note that instantiating your tracer within your settings.py file can be problematic
# for some tracers (e.g. https://github.com/jaegertracing/jaeger-client-python/issues/60).
# If this is the case, using deferred initialization via SIGNALFX_SET_GLOBAL_TRACER or
# setting to opentracing.tracer with global initialization occurring in a custom configuration
# view is recommended.
#
# Please note that you must use a version of django_opentracing
# that supports lazy tracer initialization, such as that provided
# by the bootstrap utility:
#
# sfx-py-trace-bootstrap
# or
# pip install 'signalfx[django]'
#
# The modified Jaeger tracer available as a package extra is able to be instantiated,
# but not actively used in your settings.py file.  It is important to wait until the app is
# fully loaded before creating any spans.
# ******************************************************************

SIGNALFX_MIDDLEWARE_CLASS = 'my_custom_project.MyTracingMiddleware'
```
