# Psycopg

- [signalfx/python-dbapi](https://github.com/signalfx/python-dbapi)
- [Official Site](http://initd.org/psycopg/)

The SignalFx Auto-instrumentor configures the OpenTracing DB API instrumentation for your Psycopg
connections.  You can enable instrumentation within your connection and `Cursor` commands by invoking the
`signalfx_tracing.auto_instrument()` function before initializing your `Connection` client object with
`psycopg2.connect()`.  To configure tracing, some tunables are provided via `psycopg2_config` to establish
the desired tracer and database commands for span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| traced_commands | [Cursor](https://www.python.org/dev/peps/pep-0249/#cursor-methods) and [Connection](https://www.python.org/dev/peps/pep-0249/#connection-methods) methods for which to create spans. | All supported: `['execute', 'executemany', 'callproc', 'commit', 'rollback']` |
| span_tags | Span tag names and values, as a dictionary, with which to tag all Psycopg spans. | `{}` |
| tracer | An instance of an OpenTracing-compatible tracer for all Psycopg traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import psycopg2_config 

import psycopg2

# ***
# The SignalFx Psycopg Auto-instrumentor works by monkey patching the psycopg2.connect() method.
# You must invoke auto_instrument() or instrument() before instantiating your client connection.
#
# from sfx_tracing import instrument
# instrument(psycopg2=True)  # or sfx_tracing.auto_instrument()
# traced_connection = psycopg2.connect(...)
#
# Accessing connect() from its parent psycopg2 module object requires no advanced instrumentation
# beyond that of pre-initialization.  If you are importing connect() from psycopg2 directly, you
# must instrument before doing so:
#
# from sfx_tracing import instrument
# instrument(psycopg2=True)  # or sfx_tracing.auto_instrument()
#
# from psycopg2 import connect
# traced_connection = connect(...)
# ***

psycopg2_config.traced_commands = ['executemany', 'rollback']  # other supported commands are
                                                               # 'execute', 'callproc', 'commit', and 'rollback'
psycopg2_config.span_tags = dict(my_helpful_identifier='green')
psycopg2_config.tracer = MyTracer()

auto_instrument()  # or instrument(psycopg2=True)

traced_connection = psycopg2.connect(...)

# In this example, any failing command/query will lead to a traced rollback().
# Successful commands will exit the context with an untraced commit().
with traced_connection as cursor:
    cursor.executemany('insert into table values (%s, %s)',
                       [('my', 'value'), ('another', 'value')])
    cursor.callproc('Function')  # untraced per psycopg2_config.traced_commands

```
