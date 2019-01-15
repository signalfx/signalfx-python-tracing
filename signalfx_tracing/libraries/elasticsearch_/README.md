# Elasticsearch

- [opentracing-contrib/python-elasticsearch](https://github.com/opentracing-contrib/python-elasticsearch)
- [Official Site](https://www.elastic.co/products/elasticsearch)

The SignalFx Auto-instrumentor configures the OpenTracing Project's Elasticsearch instrumentation for your Elasticsearch
2.0+ clients.  You can enable instrumentation of your client functionality with a call to the
`signalfx_tracing.auto_instrument()` function before initializing your `Elasticsearch` or
`elasticsearch.transport.Transport` object. To configure tracing, some tunables are provided via `elasticsearch_config`
to establish the desired tracer and operation name prefix.

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| prefix | The prefix to use in all span operation names  | `'Elasticsearch'` |
| tracer | An instance of an OpenTracing-compatible tracer for all Elasticsearch traces. | `opentracing.tracer` |

```python
# my_app.py
import datetime

from signalfx_tracing.libraries import elasticsearch_config
from signalfx_tracing import auto_instrument, instrument
import elasticsearch

# ***
# The SignalFx Elasticsearch auto-instrumentor works by monkey patching elasticsearch.transport.Transport creation.
# You must invoke auto_instrument() or instrument() before instantiating your Elasticsearch client.
#
# from sfx_tracing import instrument
# instrument(elasticsearch=True)  # or sfx_tracing.auto_instrument()
# instrumented_client = elasticsearch.Elasticsearch(...)
#
# Importing Elasticsearch from its parent elasticsearch module object requires no advanced instrumentation
# beyond that of pre-initialization:
#
# from sfx_tracing import instrument
# from elasticsearch import Elasticsearch
#
# instrument(elasticsearch=True)  # or sfx_tracing.auto_instrument()
# instrumented_client = Elasticsearch(...)
#
# ***

elasticsearch_config.prefix = 'MyInformativePrefix'

# Ignored if tracer argument provided to instrument() or auto_instrument()
elasticsearch_config.tracer = MyTracer()

auto_instrument()  # or instrument(elasticsearch=True)

es = elasticsearch.Elasticsearch()  # Traced client
es.index(index='my-index', doc_type='my-type', id=1, body={'my': 'data', 'timestamp': datetime.now()})  # Traced methods
es.get(index='my-index', doc_type='my-type', id=1)
```
