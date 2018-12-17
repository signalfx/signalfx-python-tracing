# Tornado

- [opentracing-contrib/python-tornado](https://github.com/opentracing-contrib/python-tornado)
- [Official Site](http://www.tornadoweb.org)

The SignalFx Auto-instrumentor configures the OpenTracing Project's Tornado instrumentation for your Tornado 4.x
or 5.x applications.  You can enable instrumentation within your `RequestHandler` and `AsyncHTTPClient` by invoking the 
`signalfx_tracing.auto_instrument()` function before initializing your application.  To configure Tornado tracing,
some tunables are provided via `tornado_config` to establish the desired tracer and request attributes for
span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| trace_all | Whether to trace all requests. | `True` |
| trace_client | Whether to trace all requests from AsyncHTTPClients. | `True` |
| traced_attributes | [Request attributes](http://www.tornadoweb.org/en/stable/httputil.html#tornado.httputil.HTTPServerRequest) to use as span tags. | `['path', 'method']` |
| tracer | An instance of an OpenTracing-compatible tracer for all Tornado traces. | `opentracing.tracer` |
| start_span_cb | A callback invoked upon new span creation.  Must take the Span and request as parameters. | `None` |

OpenTracing 2.0 introduced the [`TornadoScopeManager`](https://github.com/opentracing/opentracing-python/blob/master/opentracing/scope_managers/tornado.py).
Due to the asynchronous nature of Tornado, it is strongly recommended that your OpenTracing-compatible tracer use
this for its scope manager.

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import tornado_config

from opentracing.scope_managers.tornado import TornadoScopeManager

import tornado.ioloop
import tornado.web  
# ***
# The OpenTracing Project's Tornado instrumentor works by monkey patching some of the
# Application, RequestHandler, and AsyncHTTPClient classes' methods.
# If importing any of these class objects from tornado.web or tornado.http_client
# directly, you must invoke auto_instrument() or instrument() before doing so.
# Accessing each from their parent module object requires no advanced instrumentation
# beyond that of pre-initialization:
#
# import tornado.web
#
# instrument(tornado=True)
# app = tornado.web.Application(...)
#
# ***

tornado_config.trace_all = True  # If False, will only trace those manually decorated with
# @tracing.trace(['my_attr', 'another_attr']):
# https://github.com/opentracing-contrib/python-tornado#tracing-individual-requests 

tornado_config.trace_client = False  # Do not trace requests made by AsyncHttpClients in your application.

tornado_config.traced_attributes = ['my_attr', 'another_attr']  # Ignored if tornado_config.trace_all is False.

# Ignored if tracer argument provided to instrument() or auto_instrument()
tornado_config.tracer = MyTracer(scope_manager=TornadoScopeManager())


def my_span_callback(span, request):
    span.set_tag('my_tag', request.attribute_of_interest)


tornado_config.start_span_cb = my_span_callback


class MyApplication(tornado.web.Application):

    ...  # your app-specific functionality


class MyRequestHandler(tornado.web.RequestHandler):

    def get(self, *args, **kwargs):
        self.write('Hi There!')

    def post(self, *args, **kwargs):
        self.write('Success!')


if __name__ == "__main__":
    auto_instrument()  # or instrument(tornado=True)
    app = MyApplication([(r'/', MyRequestHandler)])
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
```
