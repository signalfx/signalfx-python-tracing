# Requests

- [signalfx/python-requests](https://github.com/signalfx/python-requests)
- [Official Site](http://docs.python-requests.org/en/master/)

The SignalFx Auto-instrumentor configures the OpenTracing Requests instrumentation for your Session commands.
You can enable instrumentation within your http client by invoking the `signalfx_tracing.auto_instrument()`
function before initializing your `Session` object or making api calls from the `requests` or `requests.api` modules. 
To configure tracing, some tunables are provided via `requests_config` to establish the desired tracer,
context propagation, and custom tag name and values for all created spans:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| propagate | Whether to propagate current trace via request headers. Only use if client reaches your services exclusively | `False` |
| span_tags | Span tag names and values, as a dictionary, with which to tag all Requests spans. | `{}` |
| tracer | An instance of an OpenTracing-compatible tracer for all Requests traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import requests_config 
import requests

# ***
# The SignalFx Requests Auto-instrumentor works by monkey patching the requests.sessions.Session.__init__() method.
# You must invoke auto_instrument() or instrument() before instantiating your client session or making requests
# from the top-level requests package. 
#
# import requests.sessions
# from sfx_tracing import instrument
# instrument(requests=True)  # or sfx_tracing.auto_instrument()
# traced_session = requests.sessions.Session()
#
# Accessing or importing Session from its parent requests or requests.sessions module objects
# requires no advanced instrumentation beyond that of pre-initialization.
#
# from sfx_tracing import instrument
# from requests import Session, get, post
# instrument(requests=True)  # or sfx_tracing.auto_instrument()
#
# traced_session = Session()
# traced_get_response = get(...)
# traced_post_response = post(...)
# ***

requests_config.propagate = True
requests_config.span_tags = dict(my_helpful_identifier='green')
requests_config.tracer = MyTracer()

auto_instrument()  # or instrument(requests=True)

traced_get_response = requests.get(...)

traced_session = requests.Session()
traced_post_response = traced_session.post(...)
```
