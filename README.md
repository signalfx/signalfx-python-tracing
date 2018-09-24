# SignalFx-Tracing: A Python OpenTracing Auto-Instrumenter

This utility provides users with the ability of automatically configuring
OpenTracing community-contributed [instrumentation libraries](https://github.com/opentracing-contrib)
for their Python 2.7 and 3.4+ applications via a single function.

```python
from signalfx_tracing import auto_instrument
from my_opentracing_compatible_tracer import Tracer

tracer = Tracer()
auto_instrument(tracer)
```

If auto-instrumentation of all applicable libraries and frameworks isn't desired,
enabling instrumentation individually can be done by specifying your target module:

```python
from signalfx_tracing import instrument, uninstrument
from my_opentracing_compatible_tracer import Tracer

tracer = Tracer()
instrument(tracer, flask=True)
# or
instrument(flask=True)  # uses the global Tracer from opentracing.tracer by default

uninstrument(flask=False)  # prevent future registrations and
                           # remove previous instrumentation, where possible.
```

## Supported Frameworks and Libraries

* [Django](./signalfx_tracing/libraries/django_/README.md) - `instrument(django=True)`
* [Flask](./signalfx_tracing/libraries/flask_/README.md) - `instrument(flask=True)`
* [PyMongo](./signalfx_tracing/libraries/pymongo_/README.md) - `instrument(pymongo=True)`
* [PyMySQL](./signalfx_tracing/libraries/pymysql_/README.md) - `instrument(pymysql=True)`
* [Tornado](./signalfx_tracing/libraries/tornado_/README.md) - `instrument(tornado=True)`

## Installation and Configuration

For the most basic installation:
```sh
 $ git clone https://github.com/signalfx/signalfx-python-tracing && pip install ./signalfx-python-tracing
```

SignalFx-Tracing works by detecting your available libraries and frameworks and configuring
instrumenters for distributed tracing via the Python
[OpenTracing API 2.0](https://pypi.org/project/opentracing/2.0.0/).  As adoption of this API
is done on a per-instrumenter basis, it's recommended that you use the helpful bootstrap
utility for obtaining and installing feature-ready instrumenter versions, instead of the basic
pip installation:

```sh
 $ ./bootstrap.py
```

Not all stable versions of OpenTracing-compatible tracers support the 2.0 API, so we provide
the option of installing a modified [Jaeger Client](https://github.com/jaegertracing/jaeger-client-python)
ready for reporting to SignalFx:

```sh
 $ ./bootstrap.py --jaeger
```

You can obtain an instance of this tracer using the `signalfx_tracing.utils.create_tracer()` helper.

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
    config={'sampler': {'type': 'const', 'param': 1},
            'logging': True},
    service_name='MyTracedApplication',
    scope_manager=TornadoScopeManager
)
```
