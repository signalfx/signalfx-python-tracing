# SignalFx-Tracing Library for Python Utilities

## sfx-py-trace-bootstrap

As the overall aim of SignalFx-Tracing is the auto-instrumentation of your application, automatically providing each
library instrumentation as it is needed is preferrable to manually managing packages for each deployment
environment or introducing a number of superfluous dependencies.  To assist in this aim, `sfx-py-trace-bootstrap` is
available to all SignalFx-Tracing installations.  It will check your current environment for traceable libraries,
uninstall any existing instrumentations for them, and install a supported instrumentation version for use with
`signalfx_tracing.instrument()`.  It will also install an updated version of the Jaeger tracer, uninstalling any
existing version beforehand.  An error is raised if any dependency conflicts are detected involving our installed
instrumentations.

Currently this utility only supports the [Pip](https://pip.pypa.io/en/stable/) package installer, and its behavior is
roughly analogous to the following process for each supported library:

```python
import subprocess

try:
    import my_supported_library
    subprocess.Popen(['pip', 'uninstall', '-y', my_supported_library_instrumentation])
    subprocess.Popen(['pip', 'install', '-U', my_supported_library_instrumentation])
except ImportError:
    pass
```

Other package installers are expected to be supported in the future, and if you have one you'd like us to support,
please feel free to open a GitHub issue.  `sfx-py-trace-bootstrap` is our preferred installation utility, but if you'd
rather manage your instrumentations manually, we also suggest cloning this repo and using the provided
[package extras](../README.md#library-and-instrumentors).

### Printing out dependencies instead of installing

The bootstrap utility accepts a `-r` or `--requirements` flag and when set, it prints out the instrumentation packages
it'd otherwise install to console. The print format is compatible with requirements.txt and can be directly appended or
added to a requirements.txt file. 

### Installing dependencies to a custom location

The boostrap utility also provides a `-t <target_dir>` or `--target <target_dir>` option for specifying the directory in which to install the dependencies.  This can be helpful when preparing serverless application bundles or images and is effectively equivalent to the `pip install -t <target_dir>` option.

## sfx-py-trace

This utility is available to all SignalFx-Tracing installations and provides users with the automatic configuration of
available instrumentations and Jaeger tracer for their Python applications via a console script, assuming they have
run `sfx-py-trace-bootstrap` or installed the required dependencies as package extras:

```sh
 $ # SIGNALFX_ENDPOINT_URL should be a deployed Smart Agent trace endpoint (http://localhost:9080/v1/trace) by default
 $ SIGNALFX_ENDPOINT_URL='http://MySmartAgent:9080/v1/trace' sfx-py-trace my_application.py --app_arg_one --app_arg_two
```

`sfx-py-trace` works by sourcing your organization access token (if provided) and registering an auto-instrumenting
[`sitecustomize`](https://docs.python.org/3.6/library/site.html) module to your `PYTHONPATH` before invoking your
target file/module and arguments with the current Python executable.  The `sitecustomize` module will create an instance
of a Jaeger tracer and set it as the OpenTracing global tracer for all instrumentations to use.  Running this should not
prevent any existing `sitecustomize` module on your `PYTHONPATH` from also running.

**Node: `sfx-py-trace` functionality will be disabled if the `SIGNALFX_TRACING_ENABLED` environment variable is `False`
or `0`.  It can still be used as an application runner, but its `site` module usage will be bypassed.**
