# Celery

- [signalfx/python-celery](https://github.com/signalfx/python-celery)
- [Official Site](https://docs.celeryproject.org/en/latest/index.html)

The SignalFx Auto-instrumentor configures the OpenTracing Celery instrumentation for your Application's tasks.
You can enable instrumentation within your application by invoking the `signalfx_tracing.auto_instrument()`
function before initializing your `Celery` object or by launching Celery workers via the `sfx-py-trace` cli as you would with the `celery` executable.
To configure tracing, some tunables are provided via `celery_config` to establish the desired tracer,
traced task publishing and context propagation, and custom tag name and values for all created spans:

| Setting name | Definition | Default value |
| -------------|------------|---------------|
| propagate | Whether to create publish-denoting spans and propagate their context via request headers for remote task execution. Suggested if countdowns are timely | `True` |
| span_tags | Span tag names and values, as a dictionary, with which to tag all instrumentation-created spans. | `{}` |
| tracer | An instance of an OpenTracing-compatible tracer for all Celery traces. | `opentracing.tracer` |

```python
# my_app.py
from signalfx_tracing import auto_instrument, instrument
from signalfx_tracing.libraries import celery_config
import celery

# ***
# The SignalFx Celery Auto-instrumentor works by monkey patching the celery.app.base.Celery.__init__() method.
# You must invoke auto_instrument() or instrument() before importing this class and instantiating your application.
#
# import celery
# from sfx_tracing import instrument
# instrument(celery=True)  # or sfx_tracing.auto_instrument()
# traced_app = celery.Celery()
#
# @traced_app.task
# def my_task():
#      return 'Executed.'
# ***

celery_config.propagate = True  # the default, False to disable
celery_config.span_tags = dict(my_helpful_identifier='green')
celery_config.tracer = MyTracer()

auto_instrument()  # or instrument(celery=True)

traced_app = celery.Celery(...)

@traced_app.task
def my_task():
     return 'Executed.'
```


## Tracing Celery Workers

To provide complete, distributed application tracing, it's necessary to enable traced worker process task execution using the [`sfx-py-trace`](../../../README.md#application-runner) application runner.  The internal mechanism for this functionality detects a target `celery` command and `worker` option from the command line arguments before registering a deferred tracer creator function via `worker_process_init` signal.  To use the application runner, replace the standard `celery` executable in your worker initialization command with `sfx-py-trace $(which celery)`.  Doing so will enable auto-instrumentation for all applicable target libraries in addition to your Celery tasks.

```bash
$ sfx-py-trace $(which celery) worker -A my_project -Q celery,my_queue
```
