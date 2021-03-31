import sys
import traceback

import opentracing
from opentracing.ext import tags

from signalfx_tracing.utils import padded_hex

SCOPE_KEY = "_signalfx_scope_key"


class TraceMiddleware(object):
    def __init__(self, tracer=None, attributes=None, trace_response_header_enabled=False):
        self.tracer = tracer or opentracing.tracer
        self.attributes = attributes or []
        self.trace_response_header_enabled = trace_response_header_enabled

    def process_request(self, req, resp):
        operation_name = req.path

        try:
            span_ctx = self.tracer.extract(opentracing.Format.HTTP_HEADERS, req.headers)
            scope = self.tracer.start_active_span(operation_name, child_of=span_ctx)
        except (
            opentracing.InvalidCarrierException,
            opentracing.SpanContextCorruptedException,
        ):
            scope = self.tracer.start_active_span(operation_name)

        span = scope.span
        span.set_tag(tags.COMPONENT, "Falcon")
        span.set_tag(tags.HTTP_METHOD, req.method)
        span.set_tag(tags.HTTP_URL, req.uri.split("?")[0])
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        for attr in self.attributes:
            attr_val = getattr(req, attr, None)
            if attr_val:
                span.set_tag(attr, attr_val)

        setattr(req, SCOPE_KEY, scope)

    def process_resource(self, req, resp, resource, params):
        scope = getattr(req, SCOPE_KEY, None)
        if scope is None:
            return
        resource_name = resource.__class__.__name__
        scope.span.set_tag("falcon.resource", resource_name)
        scope.span.set_operation_name(
            "{0}.on_{1}".format(resource_name, req.method.lower())
        )

    def process_response(self, req, resp, resource, req_succeeded=None):
        scope = getattr(req, SCOPE_KEY, None)
        if scope is None:
            return

        status = resp.status

        if resource is None:
            status = "404"

        err_type, exc, tb = sys.exc_info()
        if err_type is not None:
            if not req_succeeded:
                if "HTTPNotFound" in err_type.__name__:
                    status = "404"
                else:
                    status = "500"
                    scope.span.set_tag(tags.ERROR, True)
                    scope.span.set_tag("sfx.error.message", str(exc))
                    scope.span.set_tag("sfx.error.object", str(exc.__class__))
                    scope.span.set_tag("sfx.error.kind", exc.__class__.__name__)
                    if tb:
                        scope.span.set_tag(
                            "sfx.error.stack", "".join(traceback.format_tb(tb))
                        )

        scope.span.set_tag(tags.HTTP_STATUS_CODE, status.split(" ")[0])

        if self.trace_response_header_enabled:
            trace_id = getattr(scope.span.context, "trace_id", 0)
            span_id = getattr(scope.span.context, "span_id", 0)
            if trace_id and span_id:
                resp.append_header("Access-Control-Expose-Headers", "Server-Timing")
                resp.append_header(
                    "Server-Timing", 'traceparent;desc="00-{trace_id}-{span_id}-01"'.format(
                        trace_id=padded_hex(trace_id),
                        span_id=padded_hex(span_id),
                    ),
                )
        scope.close()
