# Copyright (C) 2020 SignalFx. All rights reserved.
import falcon


class HelloWorldResource(object):
    def _handle(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = "Hello World"

    def on_get(self, req, resp):
        return self._handle(req, resp)

    def on_post(self, req, resp):
        return self._handle(req, resp)

    def on_put(self, req, resp):
        return self._handle(req, resp)

    def on_patch(self, req, resp):
        return self._handle(req, resp)

    def on_options(self, req, resp):
        return self._handle(req, resp)

    def on_delete(self, req, resp):
        return self._handle(req, resp)

    def on_head(self, req, resp):
        return self._handle(req, resp)


class ErrorResource(object):
    def _handle(self, req, resp):
        print(undefined)  # noqa: F821

    def on_get(self, req, resp):
        return self._handle(req, resp)

    def on_post(self, req, resp):
        return self._handle(req, resp)

    def on_put(self, req, resp):
        return self._handle(req, resp)

    def on_patch(self, req, resp):
        return self._handle(req, resp)

    def on_options(self, req, resp):
        return self._handle(req, resp)

    def on_delete(self, req, resp):
        return self._handle(req, resp)

    def on_head(self, req, resp):
        return self._handle(req, resp)


app = falcon.API()

app.add_route("/hello", HelloWorldResource())
app.add_route("/error", ErrorResource())
