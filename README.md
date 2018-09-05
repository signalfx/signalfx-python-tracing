# SignalFx Python Auto-Instrumenter

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
instrument(tracer, django=True)
# or
instrument(django=True)  # uses the global Tracer from opentracing.tracer by default

uninstrument(django=False)  # removes previous instrumentation
```

## Supported Frameworks and Libraries

* [Django](./signalfx_tracing/libraries/django_/README.md) - `instrument(django=True)`
