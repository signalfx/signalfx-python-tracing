# SignalFx-Tracing Library for Python: An OpenTracing Auto-Instrumentor

This utility provides users with the ability of automatically configuring
OpenTracing 2.0-compatible community-contributed [instrumentation libraries](https://github.com/opentracing-contrib)
for their Python 2.7 and 3.4+ applications via a single function.

```python
from signalfx_tracing import auto_instrument

from my_opentracing_2_dot_0_compatible_tracer_lib import Tracer

tracer = Tracer()
auto_instrument(tracer)
```

If auto-instrumentation of all applicable libraries and frameworks isn't desired,
enabling instrumentation individually can be done by specifying your target module:

```python
from signalfx_tracing import instrument, uninstrument

from my_opentracing_2_dot_0_compatible_tracer import Tracer

tracer = Tracer()
instrument(tracer, flask=True)
# or
instrument(flask=True)  # uses the global Tracer from opentracing.tracer by default

import flask

traced_app = flask.Flask('MyTracedApplication')

@traced_app.route('/hello_world')
def traced_route():
    # Obtain active span created by traced middleware
    span = tracer.scope_manager.active.span
    span.set_tag('Hello', 'World')
    span.log_kv({'event': 'initiated'})
    return 'Hello!'  # Span is automatically finished after request handler

uninstrument('flask')  # prevent future registrations

untraced_app = flask.Flask('MyUntracedApplication')

@untraced_app.route('/untraced_hello_world')
def untraced_route():
    return 'Goodbye!'
```

## Supported Frameworks and Libraries

* [Django 1.8+](./signalfx_tracing/libraries/django_/README.md) - `instrument(django=True)`
* [Flask 0.10+](./signalfx_tracing/libraries/flask_/README.md) - `instrument(flask=True)`
* [PyMongo 3.1+](./signalfx_tracing/libraries/pymongo_/README.md) - `instrument(pymongo=True)`
* [PyMySQL 0.8+](./signalfx_tracing/libraries/pymysql_/README.md) - `instrument(pymysql=True)`
* [Redis-Py 2.10](./signalfx_tracing/libraries/redis_/README.md) - `instrument(redis=True)`
* [Requests 2.0+](./signalfx_tracing/libraries/requests_/README.md) - `instrument(requests=True)`
* [Tornado 4.3+](./signalfx_tracing/libraries/tornado_/README.md) - `instrument(tornado=True)`

## Installation and Configuration

The SignalFx-Tracing Library for Python works by detecting your available libraries and frameworks and configuring
instrumentors for distributed tracing via the Python
[OpenTracing API 2.0](https://pypi.org/project/opentracing/2.0.0/).  As adoption of this API
is done on a per-instrumentor basis, it's recommended that you use the helpful bootstrap
utility for obtaining and installing feature-ready instrumentor versions:

```sh
 $ ./bootstrap.py
```

For example, if your environment has Requests and Flask in its Python path, the corresponding OpenTracing
instrumentors will be pip installed.  Again, since OpenTracing-Contrib instrumentation support of API 2.0 is not
ubiquitous, this bootstrap selectively installs custom instrumentors listed in
[the requirements file](./requirements.txt).  As such, we suggest being sure to uninstall any previous
instrumentor versions before running the bootstrapper, ideally in a clean environment.

Not all stable versions of OpenTracing-compatible tracers support the 2.0 API, so we provide the option
of, and highly recommend, installing a modified [Jaeger Client](https://github.com/jaegertracing/jaeger-client-python)
ready for reporting to SignalFx:

```sh
 $ ./bootstrap.py --jaeger
```

You can obtain an instance of this tracer using the `signalfx_tracing.utils.create_tracer()` helper.  By default
it will enable tracing with constant sampling (100% chance of tracing) and report each span directly to SignalFx.
Where applicable, context propagation will be done via [B3 headers](https://github.com/openzipkin/b3-propagation).

```python
from signalfx_tracing import create_tracer

# sets the global opentracing.tracer by default:
tracer = create_tracer()  # uses 'SIGNALFX_ACCESS_TOKEN' environment variable if provided

# or directly provide your organization access token if not using the Smart Agent or Smart Gateway to analyze spans:
tracer = create_tracer('<OrganizationAccessToken>', ...)

# or to disable setting the global tracer:
tracer = create_tracer(set_global=False)
```

All other `create_tracer()` arguments are those that can be passed to a `jaeger_client.Config` constructor:
```python
from opentracing.scope_managers.tornado import TornadoScopeManager
from signalfx_tracing import create_tracer

tracer = create_tracer(
    '<OrganizationAccessToken>',
    config={'sampler': {'type': 'probabilistic', 'param': .05 }, 
    # 5% chance of tracing: 'sampler': {'type': 'const', 'param': 1} by default
            'logging': True},
    service_name='MyTracedApplication',
    jaeger_endpoint='http://localhost:9080/v1/trace',
    scope_manager=TornadoScopeManager  # Necessary for span scope in Tornado applications
)
```

If a `config` dictionary isn't provided or doesn't specify the desired items for your tracer, the following environment
variables are checked for before selecting a default value:

| Config kwarg | environment variable | default value |
|--------------|----------------------|---------------|
| `service_name` | `SIGNALFX_SERVICE_NAME` | `'SignalFx-Tracing'` |
| `jaeger_endpoint` | `SIGNALFX_INGEST_URL` | `'https://ingest.signalfx.com/v1/trace'` |
| `jaeger_password` | `SIGNALFX_ACCESS_TOKEN` | `None` |
| `['sampler']['type']` | `SIGNALFX_SAMPLER_TYPE` | `'const'` |
| `['sampler']['param']` | `SIGNALFX_SAMPLER_PARAM` | `1` |
| `propagation` | `SIGNALFX_PROPAGATION` | `'b3'` |


## Usage

### Application Runner
The SignalFx-Tracing Library for Python's auto-instrumentation configuration can be performed while loading
your framework-based and library-utilizing application as described in the corresponding
[instrumentation instructions](#supported-frameworks-and-libraries).
However, if you have installed the recommend Jaeger client (`./bootstrap.py --jaeger`) and would like to
automatically instrument your applicable program with the default settings, a helpful `sfx-py-trace` entry point
is provided by the installer:

```sh
 $ SIGNALFX_INGEST_URL='http://localhost:9080/v1/trace' sfx-py-trace my_application.py --app_arg_one --app_arg_two
 # not providing an access token assumes usage of the Smart Agent and/or Smart Gateway
 $ SIGNALFX_ACCESS_TOKEN=<OrganizationAccessToken> sfx-py-trace my_application.py --app_arg_one --app_arg_two
 # or
 $ sfx-py-trace --token <OrganizationAccessToken> my_application.py --app_arg_one --app_arg_two
```

**Note: `sfx-py-trace` cannot, at this time, enable auto-instrumentation of Django projects, as the instrumentor
application must be added to the project settings' installed apps for lazy tracer creation.**

This command line script loader will create a Jaeger tracer instance using the access token specified via
environment variable or argument to report your spans to SignalFx.  It will then call `auto_instrument()` before
running your target application file in its own module namespace.  It's important to note that due to potential
deadlocks in importing forking code, a Jaeger tracer cannot be initialized as a side effect of an import statement
(see: [Python threading doc](https://docs.python.org/2/library/threading.html#importing-in-threaded-code) and
[known Jaeger issue](https://github.com/jaegertracing/jaeger-client-python/issues/60#issuecomment-318909730)).

Because of this constraint, the `sfx-py-trace` utility is not a substitute for a system Python executable and
must be provided a target Python script or path with `__main__` module.  There are plans to remove Jaeger's
Tornado dependency that will remove this restriction in the future and allow expanded functionality.

### Trace Decorator
Not all applications follow the basic architectural patterns allowed by their frameworks, and no single tool will be
able to represent all use cases without user input.  To meaningfully unite isolated traces into a single, more
representative structure, or to decompose large spans into functional units, manual instrumentation will
become necessary.  The SignalFx-Tracing Library provides a helpful function decorator to automatically create spans
for tracing your custom logic:

```python
from signalfx_tracing import trace
import opentracing

from my_app import annotate, compute, report


@trace  # uses global opentracing.tracer set by signalfx_tracing.utils.create_tracer()
def my_function(arg):  # default span operation name is the name of the function
    # span will automatically trace duration of my_function() without any modifications necessary
    annotated = annotate(arg)
    return MyBusinessLogic().my_other_function(annotated)


class MyBusinessLogic:

    @classmethod  # It's necessary to declare @trace after @classmethod and @staticmethod
    @trace('MyOperation')  # Specify span operation name
    def my_other_function(cls, arg):
        # Using OpenTracing api, it's possible to modify current spans.
        # This active span is 'MyOperation', the current traced function and child of 'my_function'.
        span = opentracing.tracer.active_span
        span.set_tag('MyAnnotation', arg)
        value = cls.my_additional_function(arg)
        return report(value)

    @staticmethod
    @trace('MyOtherOperation',  # Specify span operation name and tags
           dict(tag_name='tag_value',
                another_tag_name='another_tag_value'))
    def my_additional_function(arg):
        span = opentracing.tracer.active_span  # This active span is 'MyOtherOperation', the child of 'MyOperation'.
        value = compute(arg)
        span.set_tag('ComputedValue', value)
        return value
```

In the above example, any invocation of `my_function()` will result in a trace consisting of at least three spans
whose relationship mirrors the call graph.  If `my_function()` were to be called from another traced function or
auto-instrumented request handler, its resulting span would be parented by that caller function's span.

**Note: As the example shows, `@trace` must be applied to traced methods before the `@classmethod` and `@staticmethod`
decorators are evaluated (declared after), as the utility doesn't account for their respective descriptor
implementations at this time. Not doing so will likely cause undesired behavior in your application.**
