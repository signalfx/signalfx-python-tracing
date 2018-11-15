# SignalFx-Tracing Library for Python: An OpenTracing Auto-Instrumenter

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

tracer = create_tracer('<MyAccessToken>', ...)  # sets the global opentracing.tracer by default

# or by using the token environment variable:
import os
os.environ['SIGNALFX_ACCESS_TOKEN'] = '<MyAccessToken>'
tracer = create_tracer()

# or to disable setting the global tracer:
tracer = create_tracer('<MyAccessToken>', set_global=False)
```

All other `create_tracer()` arguments are those that can be passed to a `jaeger_client.Config` constructor:
```python
from opentracing.scope_managers.tornado import TornadoScopeManager
from signalfx_tracing import create_tracer

tracer = create_tracer(
    '<MyAccessToken>',
    config={'sampler': {'type': 'probabilistic', 'param': .05 }, 
    # 5% chance of tracing: 'sampler': {'type': 'const', 'param': 1} by default
            'logging': True},
    service_name='MyTracedApplication',
    scope_manager=TornadoScopeManager  # Necessary for span scope in Tornado applications
)
```

## Usage

The SignalFx-Tracing Library for Python's auto-instrumentation configuration can be performed while loading
your framework-based and library-utilizing application as described in the corresponding
[instrumentation instructions](#supported-frameworks-and-libraries).
However, if you have installed the recommend Jaeger client (`./bootstrap.py --jaeger`) and would like to
automatically instrument your applicable program with the default settings, a helpful `sfx-py-trace` entry point
is provided by the installer:

```sh
 $ SIGNALFX_ACCESS_TOKEN=<MyAccessToken> sfx-py-trace my_application.py --app_arg_one --app_arg_two
 # or
 $ sfx-py-trace --token <MyAccessToken> my_application.py --app_arg_one --app_arg_two
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
