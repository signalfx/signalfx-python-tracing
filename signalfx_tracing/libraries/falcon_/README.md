# Falcon 

- [Official Site](https://falconframework.org/)

The SignalFx Auto-instrumentor ships with Falcon instrumentation for your Falcon 2.0+
applications.  You can enable instrumentation within your by invoking the
`signalfx_tracing.auto_instrument()` function before initializing your `Falcon` application object.
To configure tracing, some tunables are provided via `falcon_config` to establish the desired tracer and
request attributes for span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| traced_attributes | [Request attributes](https://falcon.readthedocs.io/en/stable/api/request_and_response.html#id1) to use as span tags. | `['path']` |
| tracer | An instance of an OpenTracing-compatible tracer for all Falcon traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, create_tracer, instrument
from signalfx_tracing.libraries import falcon_config

import falcon 

# ***
# The SignalFx Falcon Auto-instrumentor works by monkey patching the falcon.API.__init__() method.
# You must invoke auto_instrument() or instrument() before instantiating your app and
# decorating its routes:
#
# from sfx_tracing import instrument
# instrument(falcon=True)  # or sfx_tracing.auto_instrument()
# instrumented_app = falcon.API(...)
#
# Importing API from its parent falcon module object requires no advanced instrumentation
# beyond that of pre-initialization:
#
# from sfx_tracing import instrument
# from falcon import API 
#
# instrument(falcon=True)  # or sfx_tracing.auto_instrument()
# instrumented_app = API(...)
# ***

falcon_config.traced_attributes = ['my_attr', 'another_attr'] 

# Ignored if tracer argument provided to instrument() or auto_instrument()
falcon_config.tracer = create_tracer()

auto_instrument()  # or instrument(falcon=True)

class HelloWorldResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = 'Hello World!'


app = falcon.API()
app.add_route('/', HelloWorldResource())
```
