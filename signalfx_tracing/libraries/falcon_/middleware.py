import sys
import traceback

import opentracing
from opentracing.ext import tags


class TraceMiddleware(object):
    def __init__(self, tracer=None, attributes=None):
        self.tracer = tracer or opentracing.tracer
        self.attributes = attributes or []

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

        req.context.signalfx_tracing_scope = scope

    def process_resource(self, req, resp, resource, params):
        scope = getattr(req.context, "signalfx_tracing_scope", None)
        if scope is None:
            return
        resource_name = resource.__class__.__name__
        scope.span.set_tag('falcon.resource', resource_name)
        scope.span.set_operation_name(
            '{0}.on_{1}'.format(resource_name, req.method.lower())
        )

    def process_response(self, req, resp, resource, req_succeeded=None):
        scope = getattr(req.context, "signalfx_tracing_scope", None)
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
        scope.close()
