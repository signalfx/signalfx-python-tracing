# SignalFx-Tracing Library for Python: An OpenTracing Auto-Instrumentor

This utility provides users with the ability of automatically configuring
OpenTracing 2.0-compatible community-contributed [instrumentation libraries](https://github.com/opentracing-contrib)
for their Python 2.7 and 3.4+ applications via a single function.

```python
from signalfx_tracing import auto_instrument, create_tracer

tracer = create_tracer(service_name='MyService')
auto_instrument(tracer)
```

If auto-instrumentation of all applicable libraries and frameworks isn't desired,
enabling instrumentation individually can be done by specifying your target module:

```python
from signalfx_tracing import create_tracer, instrument, uninstrument

tracer = create_tracer()
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

**Note: Both `instrument()` and `auto_instrument()` invocations can be converted to no-ops if the
`SIGNALFX_TRACING_ENABLED` environment variable is set to `False` or `0`.  This can be helpful when developing your
auto-instrumented application locally or in test environments.**

## Supported Frameworks and Libraries

* [Django 1.8+](./signalfx_tracing/libraries/django_/README.md) - `instrument(django=True)`
* [Elasticsearch 2.0+](./signalfx_tracing/libraries/elasticsearch_/README.md) - `instrument(elasticsearch=True)`
* [Flask 0.10+](./signalfx_tracing/libraries/flask_/README.md) - `instrument(flask=True)`
* [Psycopg 2.7+](./signalfx_tracing/libraries/psycopg2_/README.md) - `instrument(psycopg2=True)`
* [PyMongo 3.1+](./signalfx_tracing/libraries/pymongo_/README.md) - `instrument(pymongo=True)`
* [PyMySQL 0.8+](./signalfx_tracing/libraries/pymysql_/README.md) - `instrument(pymysql=True)`
* [Redis-Py 2.10](./signalfx_tracing/libraries/redis_/README.md) - `instrument(redis=True)`
* [Requests 2.0+](./signalfx_tracing/libraries/requests_/README.md) - `instrument(requests=True)`
* [Tornado 4.3+](./signalfx_tracing/libraries/tornado_/README.md) - `instrument(tornado=True)`

## Installation and Configuration

### Library and Instrumentors
The SignalFx-Tracing Library for Python works by detecting your libraries and frameworks and configuring available
instrumentors for distributed tracing via the Python [OpenTracing API 2.0](https://pypi.org/project/opentracing/2.0.0/). 
By default, its footprint is small and doesn't declare any instrumentors as dependencies. That is, it operates on the
assumption that you have 2.0-compatible instrumentors installed as needed. As adoption of this API is done on a
per-instrumentor basis, it's highly recommended you use the helpful [bootstrap utility](./scripts/README.md) for
obtaining and installing any applicable, feature-ready instrumentors along with a compatible tracer:

```sh
  $ pip install signalfx-tracing
  $ sfx-py-trace-bootstrap
```

For example, if your environment has Requests and Flask in its Python path, the corresponding OpenTracing
instrumentors will be pip installed.  Again, since OpenTracing-Contrib instrumentation support of API 2.0 is not
ubiquitous, this bootstrap selectively installs custom instrumentors listed in
[the instrumentor requirements file](./requirements-inst.txt).  As such, we suggest being sure to uninstall any previous
instrumentor versions before running the bootstrapper, ideally in a clean environment.

To run the instrumentor bootstrap process without installing the suggested tracer, you can run the following from this
project's source tree:

```sh
  $ scripts/bootstrap.py --deps-only
```

You can also specify a target installation directory, which will include the most recent `signalfx-tracing` as provided
by PyPI:

```sh
  $ sfx-py-trace-bootstrap -t /my/site/packages/directory
```

It's also possible to install the supported instrumentors as package extras from a cloned repository:

```bash
  $ git clone https://github.com/signalfx/signalfx-python-tracing.git
  # Supported extras are dbapi, django, flask, pymongo, pymysql, redis, requests, tornado
  $ pip install './signalfx-python-tracing[django,redis,requests]'
```

**Note: For pip versions earlier than 18.0, it's necessary to include `--process-dependency-links` to
obtain the desired instrumentor versions.**

```bash
  $ git clone https://github.com/signalfx/signalfx-python-tracing.git
  # pip versions <18.0
  $ pip install --process-dependency-links './signalfx-python-tracing[jaeger,tornado]'
```

### Tracer
Not all stable versions of OpenTracing-compatible tracers support the 2.0 API, so we provide
and recommend installing a modified [Jaeger Client](https://github.com/jaegertracing/jaeger-client-python)
ready for reporting to SignalFx. You can obtain an instance of the suggested Jaeger tracer using a
 `signalfx_tracing.utils.create_tracer()` helper, provided you've run:

```sh
  $ sfx-py-trace-bootstrap

  # or as package extra
  $ pip install './signalfx-python-tracing[jaeger]'
  # please use required --process-dependency-links for pip versions <18.0 
  $ pip install --process-dependency-links './signalfx-python-tracing[jaeger]'

  # or from project source tree, along with applicable instrumentors
  $ scripts/bootstrap.py --jaeger

  # or to avoid applicable instrumentors
  $ scripts/bootstrap.py --jaeger-only
```

By default `create_tracer()` will enable tracing with constant sampling (100% chance of tracing) and report each span
directly to SignalFx. Where applicable, context propagation will be done via
[B3 headers](https://github.com/openzipkin/b3-propagation).

```python
from signalfx_tracing import create_tracer

# sets the global opentracing.tracer by default:
tracer = create_tracer()  # uses 'SIGNALFX_ACCESS_TOKEN' environment variable if provided

# or directly provide your organization access token if not using the Smart Agent to analyze spans:
tracer = create_tracer('<OrganizationAccessToken>', ...)

# or to disable setting the global tracer:
tracer = create_tracer(set_global=False)
```

All other `create_tracer()` arguments are those that can be passed to a `jaeger_client.Config` constructor:
```python
from opentracing.scope_managers.tornado import TornadoScopeManager
from signalfx_tracing import create_tracer

tracer = create_tracer(
    '<OptionalOrganizationAccessToken>',
    config=dict(jaeger_endpoint='http://localhost:9080/v1/trace'),
    service_name='MyTracedApplication',
    scope_manager=TornadoScopeManager  # Necessary for span scope in Tornado applications
)
```

If a `config` dictionary isn't provided or doesn't specify the desired items for your tracer, the following environment
variables are checked for before selecting a default value:

| Config kwarg | environment variable | default value |
|--------------|----------------------|---------------|
| `service_name` | `SIGNALFX_SERVICE_NAME` | `'SignalFx-Tracing'` |
| `jaeger_endpoint` | `SIGNALFX_ENDPOINT_URL` | `'http://localhost:9080/v1/trace'` |
| `jaeger_password` | `SIGNALFX_ACCESS_TOKEN` | `None` |
| `['sampler']['type']` | `SIGNALFX_SAMPLER_TYPE` | `'const'` |
| `['sampler']['param']` | `SIGNALFX_SAMPLER_PARAM` | `1` |
| `propagation` | `SIGNALFX_PROPAGATION` | `'b3'` |


**Note: By default `create_tracer()` will store the initial tracer created upon first invocation and return
that instance for subsequent invocations.  If for some reason multiple tracers are needed, you can provide
`create_tracer(allow_multiple=True)` as a named argument.**

## Usage

### Application Runner
The SignalFx-Tracing Library for Python's auto-instrumentation configuration can be performed while loading
your framework-based and library-utilizing application as described in the corresponding
[instrumentation instructions](#supported-frameworks-and-libraries).
However, if you have installed the recommended [Jaeger client](#Tracer) (`sfx-py-trace-bootstrap`) and would like to
automatically instrument your applicable program with the default settings, a helpful `sfx-py-trace` entry point
is provided by the installer:

```sh
  $ sfx-py-trace my_application.py --app_arg_one --app_arg_two
  # Or if your Smart Agent is not available at the default endpoint url:
  $ SIGNALFX_ENDPOINT_URL='http://MySmartAgent:9080/v1/trace' sfx-py-trace my_application.py
```

**Note: `sfx-py-trace` cannot, at this time, enable auto-instrumentation of Django projects, as the `signalfx_tracing` 
instrumentor application must still be added to the project settings' installed apps.**

This command line script loader will create a Jaeger tracer instance using the access token specified via
environment variable or argument to report your spans to SignalFx.  It will then call `auto_instrument()` before
running your target application file in its own module namespace.  It's important to note that due to potential
deadlocks in importing forking code, the standard Jaeger tracer cannot be initialized as a side effect of an import
statement (see: [Python threading doc](https://docs.python.org/2/library/threading.html#importing-in-threaded-code) and
[known Jaeger issue](https://github.com/jaegertracing/jaeger-client-python/issues/60#issuecomment-318909730)).
Because of this issue, and for general lack of HTTP reporting support, we highly suggest you use our modified [Jaeger
tracer](#Tracer) that provides deferred thread creation to avoid this constraint.

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
