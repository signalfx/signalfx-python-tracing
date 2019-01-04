# PyMySQL

- [signalfx/python-dbapi](https://github.com/signalfx/python-dbapi)
- [Official Site](https://pymysql.readthedocs.io)

The SignalFx Auto-instrumentor configures the OpenTracing DB API instrumentation for your PyMySQL
connections.  You can enable instrumentation within your connection and `Cursor` commands by invoking the
`signalfx_tracing.auto_instrument()` function before initializing your `Connection` client object with
`pymysql.connect()`.  To configure tracing, some tunables are provided via `pymysql_config` to establish
the desired tracer and database commands for span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| traced_commands | [Cursor](https://www.python.org/dev/peps/pep-0249/#cursor-methods) and [Connection](https://www.python.org/dev/peps/pep-0249/#connection-methods) methods for which to create spans. | All supported: `['execute', 'executemany', 'callproc', 'commit', 'rollback']` |
| span_tags | Span tag names and values, as a dictionary, with which to tag all PyMySQL spans. | `{}` |
| tracer | An instance of an OpenTracing-compatible tracer for all PyMySQL traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import pymysql_config 

import pymysql

# ***
# The SignalFx PyMySQL Auto-instrumentor works by monkey patching the pymysql.connect() method.
# You must invoke auto_instrument() or instrument() before instantiating your client connection.
#
# from sfx_tracing import instrument
# instrument(pymysql=True)  # or sfx_tracing.auto_instrument()
# traced_connection = pymysql.connect(...)
#
# Accessing connect() from its parent pymysql module object requires no advanced instrumentation
# beyond that of pre-initialization.  If you are importing connect() from pymysql directly, you
# must instrument before doing so:
#
# from sfx_tracing import instrument
# instrument(pymysql=True)  # or sfx_tracing.auto_instrument()
#
# from pymysql import connect
# traced_connection = connect(...)
# ***

pymysql_config.traced_commands = ['executemany', 'rollback']  # other supported commands are
                                                              # 'execute', 'callproc', 'commit', and 'rollback'
pymysql_config.span_tags = dict(my_helpful_identifier='green')
pymysql_config.tracer = MyTracer()

auto_instrument()  # or instrument(pymysql=True)

traced_connection = pymysql.connect(...)

# In this example, any failing command/query will lead to a traced rollback().
# Successful commands will exit the context with an untraced commit().
with traced_connection as cursor:
    cursor.executemany('insert into table values (%s, %s)',
                       [('my', 'value'), ('another', 'value')])
    cursor.callproc('StoredProcedure')  # untraced per pymysql_config.traced_commands

```
