from opentracing.ext.tags import *  # noqa


# The type or "kind" of an error (only for event="error" logs). E.g.,
# "Exception", "OSError"
ERROR_KIND = "sfx.error.kind"

# The actual Exception/Error object instance itself. E.g., A python
# exceptions.NameError instance
ERROR_OBJECT = "sfx.error.object"

# A concise, human-readable, one-line error message explaining the event. E.g.,
# "Could not connect to backend", "Cache invalidation succeeded"
ERROR_MESSAGE = "sfx.error.message"

# A stack trace in platform-conventional format; may or may not pertain to
# an error.
ERROR_STACK = "sfx.error.stack"

# SFX_TRACING_VERSION specifies the SignalFx tracing library that generated the span.
SFX_TRACING_VERSION = "signalfx.tracing.version"

# SFX_TRACING_LIBRARY specifies the SignalFx tracing library version.
SFX_TRACING_LIBRARY = "signalfx.tracing.library"

SFX_ENVIRONMENT = "environment"
