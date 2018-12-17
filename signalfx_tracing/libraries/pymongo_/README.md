# PyMongo

- [signalfx/python-pymongo](https://github.com/signalfx/python-pymongo)
- [Official Site](http://api.mongodb.com/python/current/index.html)

The SignalFx Auto-instrumentor configures the OpenTracing PyMongo instrumentation for your MongoClient
commands.  You can enable instrumentation within your client, database, and collection commands by invoking
the `signalfx_tracing.auto_instrument()` function before initializing your `MongoClient` object.
To configure tracing, some tunables are provided via `pymongo_config` to establish the desired tracer and
custom tag name and values for all created spans:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| span_tags | Span tag names and values, as a dictionary, with which to tag all PyMongo spans. | `{}` |
| tracer | An instance of an OpenTracing-compatible tracer for all PyMongo traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import pymongo_config 

import pymongo

# ***
# The SignalFx PyMongo Auto-instrumentor works by monkey patching the MongoClient.__init__() method.
# You must invoke auto_instrument() or instrument() before instantiating your client. 
#
# from sfx_tracing import instrument
# instrument(pymongo=True)  # or sfx_tracing.auto_instrument()
# traced_client = pymongo.MongoClient(...)
#
# Importing MongoClient from its parent pymongo module object requires no advanced instrumentation
# beyond that of pre-initialization:
#
# from sfx_tracing import instrument
# from pymongo import MongoClient
#
# instrument(pymongo=True)  # or sfx_tracing.auto_instrument()
# traced_client = MongoClient(...)
# ***

pymongo_config.span_tags = dict(my_helpful_identifier='green')
pymongo_config.tracer = MyTracer()

auto_instrument()  # or instrument(pymongo=True)

traced_client = pymongo.MongoClient(...)
traced_collection = traced_client['MyDatabase']['MyCollection']

# Commands made to the Mongo instance/cluster will be traced.
traced_collection.insert_many(...)  
```
