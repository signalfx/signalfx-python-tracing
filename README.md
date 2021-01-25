# Deprecation Notice

:warning: **Please be advised this project is deprecated. Only critical security
fixes and bugs will be provided.** :warning:

We recommend using our [Splunk Distribution of OpenTelemetry
Python](https://github.com/signalfx/splunk-otel-python) going forward, which offers
the same capabilities and fully supports the OpenTelemetry standard.

# SignalFx Tracing Library for Python

The SignalFx Tracing Library for Python automatically instruments your
Python 2.7 or 3.4+ application to capture and report distributed traces to
SignalFx with a single function. The library does so by configuring an
OpenTracing-compatible tracer you can use to capture and export trace spans.
You can use the tracer to embed custom instrumentation in the automatically
generated traces.

The SignalFx-Tracing Library for Python works by detecting your libraries and
frameworks and configuring available instrumentors for distributed tracing via
the Python [OpenTracing API 2.0](https://pypi.org/project/opentracing/2.0.0/).
By default, its footprint is small and doesn't declare any instrumentors as
dependencies.

The library provides helpful [utilities](./scripts/README.md) to
install each applicable instrumentor along with a compatible tracer. The
bootstrap utility selectively installs custom instrumentors listed in the
[instrumentor requirements file](./requirements-inst.txt). The application
runner creates a tracer with a modified 
[Jaeger Client](https://github.com/signalfx/jaeger-client-python) ready for
reporting to SignalFx and auto-instruments your app without any required
code changes.

The library enables tracing with constant sampling (i.e., 100% chance of tracing)
and reports each span to SignalFx. Where applicable, context propagation uses
[B3 headers](https://github.com/openzipkin/b3-propagation).

For more information about automatically instrumenting your application, see
[Automatically instrument a Python application](#Automatically-instrument-a-Python-application).

If you don't want to automatically instrument all applicable libraries and
frameworks, specify your target module to manually instrument your Python
application. For more information about manually instrumenting your application,
see [Manually instrument a Python application](#Manually-instrument-a-Python-application).

## Requirements and supported software

These are the supported libraries.

| Library | Versions supported | Instrumentation name(s) | Notes |
| ---     | ---                | ---                     | ---   |
|[Celery](./signalfx_tracing/libraries/celery_/README.md) | 3.1+ | `instrument(celery=True)` | |
| [Django](./signalfx_tracing/libraries/django_/README.md) | 1.8+ | `instrument(django=True)` | Requires `signalfx_tracing` in the project's installed applications. |
| [Elasticsearch](./signalfx_tracing/libraries/elasticsearch_/README.md) | 2.0+ | `instrument(elasticsearch=True)` | |
| [Falcon](./signalfx_tracing/libraries/falcon_/README.md) | 2.0+ | `instrument(falcon=True)` | |
| [Flask](./signalfx_tracing/libraries/flask_/README.md) | 0.10+ | `instrument(flask=True)` | |
| [Psycopg](./signalfx_tracing/libraries/psycopg2_/README.md) | 2.7+ | `instrument(psycopg2=True)` | |
| [PyMongo](./signalfx_tracing/libraries/pymongo_/README.md) | 3.1+ | `instrument(pymongo=True)` | |
| [PyMySQL](./signalfx_tracing/libraries/pymysql_/README.md) | 0.8+ | `instrument(pymysql=True)` | |
| [Redis-Py](./signalfx_tracing/libraries/redis_/README.md) | 2.10+ | `instrument(redis=True)` | |
| [Requests](./signalfx_tracing/libraries/requests_/README.md) | 2.0+ | `instrument(requests=True)` | |
| [Tornado 4.3-6.x](./signalfx_tracing/libraries/tornado_/README.md) | 4.3-6.x | `instrument(tornado=True)` | |

If you don't provide a  `config` dictionary or don't specify the following items
for your tracer, these environment variables are checked before selecting a
default value:

| Config kwarg | environment variable | default value | notes |
|--------------|----------------------|---------------|-------|
| `service_name` | `SIGNALFX_SERVICE_NAME` | `'SignalFx-Tracing'` | The name to identify the service in SignalFx. |
| `jaeger_endpoint` | `SIGNALFX_ENDPOINT_URL` | `'http://localhost:9080/v1/trace'` | The endpoint the tracer sends spans to. Send spans to a Smart Agent, OpenTelemetry Collector, or a SignalFx ingest endpoint. |
| `jaeger_password` | `SIGNALFX_ACCESS_TOKEN` | `None` | The SignalFx organization access token. |
| `N/A` | `SIGNALFX_RECORDED_VALUE_MAX_LENGTH` | `1200` | The maximum length an attribute value can have. Values longer than this are truncated. |

## Automatically instrument a Python application

Install the tracing library, use the `sfx-py-trace-bootstrap` utility to
configure instrumentation and create a tracer, and automatically instrument your
application with the `sfx-py-trace` utility. Install instrumentation and the
Jaeger tracer with the [bootstrap utility](./scripts/README.md#sfx-py-trace-bootstrap) and
automatically instrument your application with the [application runner](./scripts/README.md#sfx-py-trace).

`sfx-py-trace` can't enable auto-instrumentation of Django projects by itself
because you have to add the `signalfx_tracing` instrumentor in the project settings'
installed applications. Once you specify the application, use `sfx-py-trace` as
described in the 
[Django instrumentation documentation](./signalfx_tracing/libraries/django_/README.md).

`sfx-py-trace` creates a Jaeger tracer instance using the access token specified
with the environment variable or argument to report your spans to SignalFx. It
then calls `auto_instrument()` before running your target application file in
its own module namespace. Due to potential deadlocks in importing forking code,
you can't initialize the standard Jaeger tracer as a side effect of an import
statement. For more information, see
[Python threading doc](https://docs.python.org/2/library/threading.html#importing-in-threaded-code) 
and [known Jaeger issue](https://github.com/jaegertracing/jaeger-client-python/issues/60#issuecomment-318909730).
Because of this issue, and for general lack of HTTP reporting support, use the
modified [Jaeger tracer](#Tracer) that provides deferred thread creation to
avoid this constraint.

`sfx-py-trace` attempts to instrument all available libraries there are
corresponding instrumentations installed on your system for. If you want to
prevent the tracing of particular libraries at run time, set the
`SIGNALFX_<LIBRARY_NAME>_ENABLED=False` environment variable when launching the
`sfx-py-trace` process. For example, to prevent auto-instrumentation of Tornado,
you could run:

```sh
  $ SIGNALFX_TORNADO_ENABLED=False sfx-py-trace my_application.py
```

The supported value of each library name is the uppercase form of the
corresponding `instrument()` [keyword argument](#Supported-Frameworks-and-Libraries).

1. Set the service name, endpoint URL, and access token:
    ```bash
    # Specify a name for the service in SignalFx.
    $ export SIGNALFX_SERVICE_NAME="your_service"
    # Set the endpoint URL for the Smart Agent, OpenTelemetry Collector, or ingest endpoint.
    $ export SIGNALFX_ENDPOINT_URL="http://localhost:9080/v1/trace"
    # If you're reporting directly to SignalFx without a Smart Agent or Collector, provide the access token for your SignalFx organization.
    $ export SIGNALFX_ACCESS_TOKEN="your_access_token"
    ```
2. Install the tracing library:
    ```bash
    $ pip install signalfx-tracing
    ```
3. Run the bootstrap utility:
    ```bash
    $ sfx-py-trace-bootstrap
    ```
4. Run the trace utility:
    ```bash
    $ sfx-py-trace your_application.py --app_arg_one --app_arg_two
    ```
    
## Manually configure the tracing library components

Manually configure each applicable instrumentor, tracer, and instrument your
application. Manually instrumenting an application is helpful when you want to
monitor more than the auto-instrumentation process configures or you want to
add custom instrumentation tags.

1. Uninstall any previous instrumentor versions. If you use the bootstrap
utility, it automatically does this for you. 
2. Install the tracing library:
      ```bash
    $ pip install signalfx-tracing
      ```
3. Install applicable instrumentors. There are a few ways to do this.
   1. Run the bootstrap utility:
        ```bash
      $ sfx-py-trace-bootstrap
        ```
   2. Run the bootstrap utility and specify a target installation directory that
   includes the most recent tracing library provided by PyPI:
        ```bash
  		$ sfx-py-trace-bootstrap -t /your/site/packages/directory 
        ```
   3. Run the bootstrap utility without installing the Jaeger tracer from your
   project's source tree:
        ```bash
  		$ scripts/bootstrap.py --deps-only
        ```
   4. Install the supported instrumentors as package extras from a cloned repository:
        ```bash
  	 	$ git clone https://github.com/signalfx/signalfx-python-tracing.git
      # View setup.py for available package extras.
      # If you're using a pip version older than version 18, include
      # --process-dependency-links in the install command.
	    $ pip install './signalfx-python-tracing[extra,extra,extra]'
      ```
4. Set the service name, endpoint URL, and access token:
    ```bash
    # Specify a name for the service in SignalFx.
    $ export SIGNALFX_SERVICE_NAME="your_service"
    # Set the endpoint URL for the Smart Agent, OpenTelemetry Collector, or ingest endpoint.
    $ export SIGNALFX_ENDPOINT_URL="http://localhost:9080/v1/trace"
    # Provide the access token for your SignalFx organization.
    $ export SIGNALFX_ACCESS_TOKEN="your_access_token"
    ```
5. Create a tracer using `signalfx_tracing.utils.create_tracer()`. This sets
the global `opentracing.tracer` by default. The tracer uses the
`SIGNALFX_ACCESS_TOKEN` environment variable. By default, `create_tracer()`
stores the initial tracer created upon first invocation and returns that instance
for subsequent invocations. If you need to use multiple tracers, you can provide
`create_tracer(allow_multiple=True)` as a named argument.
      ```python
      from signalfx_tracing import create_tracer

      tracer = create_tracer()
      ```
    If you're instrumenting a Tornado application, import the Tornado Scope Manager
    when you create the tracer:
      ```python
      from tornado_opentracing.scope_managers import TornadoScopeManager
      from signalfx_tracing import create_tracer

      tracer = create_tracer(
        scope_manager=TornadoScopeManager
      )
      ```

6. Instrument your code. You can automatically instrument your code or manually
instrument your code. You can convert `instrument()` and `auto_instrument()` to
no-ops by setting the `SIGNALFX_TRACING_ENABLED` environment variable to `False`
or `0`. This can be helpful when you're developing your application locally or
deploying in a test environment.
   1. Automatically instrument your code:
      ```python
      from signalfx_tracing import auto_instrument, create_tracer
      tracer = create_tracer()
      auto_instrument(tracer)
      ```
   2. Manually instrument your code:
      ```python
      from signalfx_tracing import create_tracer, instrument

      tracer = create_tracer()
      instrument(tracer, flask=True)
      # or
      instrument(flask=True)  # uses the global Tracer from opentracing.tracer by default
      
      import flask

      traced_app = flask.Flask('MyTracedApplication')
      
      @traced_app.route('/hello_world')
      def traced_route():
        # Obtain active span created by traced middleware
        span = tracer.scope_manager.active.span
        span.set_tag('Hello', 'World')
        span.log_kv({'event': 'initiated'})
        return 'Hello!'  # Span is automatically finished after request handler
      ```
1. Automatically create spans for custom application logic with a trace decorator:
      ```python
      from signalfx_tracing import trace
      import opentracing

      from my_app import annotate, compute, report


      @trace  # uses global opentracing.tracer set by signalfx_tracing.utils.create_tracer()
      def my_function(arg):  # default span operation name is the name of the function
          # span will automatically trace duration of my_function() without any modifications necessary
          annotated = annotate(arg)
          return MyBusinessLogic().my_other_function(annotated)


      class MyBusinessLogic:

          @classmethod  # It's necessary to declare @trace after @classmethod and @staticmethod
          @trace('MyOperation')  # Specify span operation name
          def my_other_function(cls, arg):
              # Using OpenTracing api, it's possible to modify current spans.
              # This active span is 'MyOperation', the current traced function and child of 'my_function'.
              span = opentracing.tracer.active_span
              span.set_tag('MyAnnotation', arg)
              value = cls.my_additional_function(arg)
              return report(value)

          @staticmethod
          @trace('MyOtherOperation',  # Specify span operation name and tags
                 tags={'tag_name':'tag_value','another_tag_name':'another_tag_value'})
          def my_additional_function(arg):
              span = opentracing.tracer.active_span  # This active span is 'MyOtherOperation', the child of 'MyOperation'.
              value = compute(arg)
              span.set_tag('ComputedValue', value)
              return value
      ```
    Any invocation of `my_function()` results in a trace consisting of at least
    three spans whose relationship mirrors the call graph. If `my_function()` were
    to be called from another traced function or auto-instrumented request handler, 
    its resulting span would be parented by that caller function's span.

## Tracer debug logging

The tracer can be configured to log debugging information by setting `SIGNALFX_TRACING_DEBUG` to `true`. This tell the tracer to log additional information that might be
helpful in understanding how it operates. Note that in order for debug logging to work, you application must initialize logging with `logging.basicConfig()` first.

## Inject trace IDs in logs

Link individual log entries with trace IDs and span IDs associated with corresponding events. The SignalFx Python instrumentation patches `logging.Logger.makeRecord` method to automatically inject trace context into all `LogRecord` objects. When `SIGNALFX_LOGS_INJECTION` environment variable is set to `true`, the logging instrumentation also sets a custom logging format to automatically inject the trace context into logs. The default format looks like the following:

```
%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [signalfx.trace_id=%(sfxTraceId)s signalfx.span_id=%(sfxSpanId)s] - %(message)s
```

If you don't want the instrumentation to set a custom logging format and would rather use your format, you can set `SIGNALFX_LOGS_INJECTION` to `false` to disable automatic injection. You can then add `%(sfxSpanId)s` and `%(sfxTraceId)s` to your log format to inject the trace context. Alternately, you can keep automatic injection enabled and pass your custom logging format to the instrumentation by setting the `SIGNALFX_LOGGING_FORMAT` env var. 

Log injection is not enabled by default and can be enabled by setting `SIGNALFX_LOGS_INJECTION` environment variable to `true`.

## Manually installing instrumentations

`sfx-py-trace-bootstrap` command automatically detects and installs the relevant instrumentations for your environment. If for some reason you cannot use the bootstrap command, you can manually install the relevant packages with pip. Following is a list of all the libraries we support and the commands to install their corresponding instrumentation packages.

| Library/Framework | Instrumentation Package |
| ----------------- | ----------------------- | 
| celery | signalfx-instrumentation-celery |
| django | signalfx-instrumentation-django |
| elasticsearch | signalfx-instrumentation-elasticsearch |
| flask | signalfx-instrumentation-flask |
| psycopg | signalfx-instrumentation-dbapi |
| pymongo | signalfx-instrumentation-pymongo |
| pymysql | signalfx-instrumentation-dbapi |
| redis | signalfx-instrumentation-redis |
| requests | signalfx-instrumentation-requests |
| tornado | signalfx-instrumentation-tornado |


### Example

If your Python app is using flask and you want to install flask instrumentation, you'd have to run 

```
pip install signalfx-instrumentation-flask
```

or add the package to your `requirements.txt` file.
