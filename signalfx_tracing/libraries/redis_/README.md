# Redis

- [opentracing-contrib/python-redis](https://github.com/opentracing-contrib/python-redis)
- [Official Site](https://redis.io/)

The SignalFx Auto-instrumentor configures the OpenTracing Redis-Py instrumentation for your 2.10+ `StrictRedis`
client commands.  You can enable instrumentation within your client, pipeline, and PubSub commands by invoking
the `signalfx_tracing.auto_instrument()` function before initializing your `StrictRedis` object.
To configure tracing, a tunable is provided via `redis_config` to establish the desired tracer:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| tracer | An instance of an OpenTracing-compatible tracer for all Redis traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import redis_config 

import redis

# ***
# The SignalFx Redis Auto-instrumentor works by monkey patching the StrictRedis.__init__() method.
# You must invoke auto_instrument() or instrument() before instantiating your client. 
#
# from sfx_tracing import instrument
# instrument(redis=True)  # or sfx_tracing.auto_instrument()
# traced_client = redis.StrictRedis(...)
#
# Importing StrictRedis from its parent redis package or redis.client module objects requires no advanced
# instrumentation beyond that of pre-initialization:
#
# from sfx_tracing import instrument
# from redis import StrictRedis
#
# instrument(redis=True)  # or sfx_tracing.auto_instrument()
# traced_client = StrictRedis(...)
# ***

redis_config.tracer = MyTracer()

auto_instrument()  # or instrument(redis=True)

# All new instances of StrictClients will have their executed commands traced
traced_client = redis.StrictRedis(...)
traced_set_response = traced_client.set('my_key', 'my_value')

another_traced_client = redis.StrictRedis(...)
traced_pubsub = another_traced_client.pubsub(...)
traced_pubsub.subscribe('MyChannel')

traced_pipeline = traced_client.pipeline()
traced_pipeline.set('some_key', 'some_value')
traced_pipeline.set('some_other_key', 'some_other_value')
traced_pipeline.execute()
```
