import tornado.testing
from tornado.httpclient import HTTPError
from tornado import version_info as tornado_version

from ._test_case import AsyncHTTPTestCase as BaseTestCase


use_wait_stop = tornado_version < (5, 0, 0)

if use_wait_stop:

    def gen_test(func):
        return func


else:
    gen_test = tornado.testing.gen_test


class AsyncHTTPTestCase(BaseTestCase):
    @gen_test
    def _http_fetch_gen(self, url, *args, **kwargs):
        try:
            response = yield self.http_client.fetch(url, *args, **kwargs)
        except HTTPError as exc:
            response = exc.response
        return response

    def http_fetch(self, url, *args, **kwargs):
        fetch = self._http_fetch_gen
        if use_wait_stop:
            fetch = super().http_fetch
        return fetch(url, *args, **kwargs)
