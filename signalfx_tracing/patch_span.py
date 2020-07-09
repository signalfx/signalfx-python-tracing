# Copyright (C) 2018-2019 SignalFx. All rights reserved.
import traceback
from wrapt import wrap_function_wrapper

from . import tags


def _wrapped_span_on_error(wrapped, instance, args, kwargs):
    def inner(span, exc_type, exc_val, exc_tb):
        if not span or not exc_val:
            return

        span.set_tag(tags.ERROR, True)
        span.set_tag(tags.ERROR_MESSAGE, str(exc_val))
        span.set_tag(tags.ERROR_OBJECT, str(exc_val.__class__))
        span.set_tag(tags.ERROR_KIND, exc_type.__name__)
        span.set_tag(tags.ERROR_STACK, traceback.format_tb(exc_tb))

    return inner(*args, **kwargs)


wrap_function_wrapper('opentracing', 'Span._on_error', _wrapped_span_on_error)
