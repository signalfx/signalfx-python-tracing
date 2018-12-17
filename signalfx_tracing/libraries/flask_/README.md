# Flask

- [opentracing-contrib/python-flask](https://github.com/opentracing-contrib/python-flask)
- [Official Site](http://flask.pocoo.org)

The SignalFx Auto-instrumentor configures the OpenTracing Project's Flask instrumentation for your Flask 0.10+
applications.  You can enable instrumentation within your app and `Blueprint` routes by invoking the
`signalfx_tracing.auto_instrument()` function before initializing your `Flask` application object.
To configure tracing, some tunables are provided via `flask_config` to establish the desired tracer and
request attributes for span tagging:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| trace_all | Whether to trace all requests. | `True` |
| traced_attributes | [Request attributes](http://flask.pocoo.org/docs/1.0/api/#flask.Request) to use as span tags. | `['path', 'method']` |
| tracer | An instance of an OpenTracing-compatible tracer for all Flask traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import flask_config

import flask

# ***
# The SignalFx Flask Auto-instrumentor works by monkey patching the Flask.__init__() method.
# You must invoke auto_instrument() or instrument() before instantiating your app and
# decorating its routes:
#
# from sfx_tracing import instrument
# instrument(flask=True)  # or sfx_tracing.auto_instrument()
# instrumented_app = flask.Flask(...)
#
# Importing Flask from its parent flask module object requires no advanced instrumentation
# beyond that of pre-initialization:
#
# from sfx_tracing import instrument
# from flask import Flask
#
# instrument(flask=True)  # or sfx_tracing.auto_instrument()
# instrumented_app = Flask(...)
# ***

flask_config.trace_all = True  # If False, will only trace those manually decorated with
# @tracer.trace('my_attr', 'another_attr'):
# https://github.com/opentracing-contrib/python-flask#trace-individual-requests
# You can access your instrumented app tracer with:
# tracer = app.config['FLASK_TRACER']

flask_config.traced_attributes = ['my_attr', 'another_attr']  # Ignored if flask_config.trace_all is False.

# Ignored if tracer argument provided to instrument() or auto_instrument()
flask_config.tracer = MyTracer()

auto_instrument()  # or instrument(flask=True)

app = flask.Flask(__name__)
bp = flask.Blueprint('form_letter', __name__)


@app.route('/healthcheck')
def healthcheck()
    self.write('In Good Spirits!')


@bp.route('/<letter>', methods=['GET', 'POST'])
def collate(letter)
    self.write('Thank You!')


app.register_blueprint(bp, url_prefix='/letters')

if __name__ == "__main__":
    app.run()
```
