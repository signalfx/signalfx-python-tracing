# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from opentracing.mocktracer import MockTracer
from opentracing.ext import tags as ext_tags
from requests.sessions import Session
import requests
import docker
import pytest

from signalfx_tracing.libraries import requests_config as config
from signalfx_tracing import instrument, uninstrument


server_port = 5678
server = 'http://localhost:{}'.format(server_port)


@pytest.fixture(scope='session')
def echo_container():
    session = docker.from_env()
    echo = session.containers.run('hashicorp/http-echo:latest', '-text="hello world"',
                                  ports={'5678/tcp': server_port}, detach=True)
    try:
        yield echo
    finally:
        echo.remove(force=True, v=True)


class TestSessionTracing(object):

    @pytest.fixture
    def session_tracing(self, echo_container):
        tracer = MockTracer()
        config.tracer = tracer
        config.propagate = True
        config.span_tags = dict(custom='tag')

        instrument(requests=True)
        try:
            yield tracer
        finally:
            uninstrument('requests')

    @pytest.fixture
    def tracer(self, session_tracing):
        return session_tracing

    @pytest.fixture
    def top_level_session(self, session_tracing):
        return requests.Session()

    @pytest.fixture
    def session(self, session_tracing):
        return Session()

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_successful_top_level_session_requests(self, tracer, top_level_session, method):
        with tracer.start_active_span('root'):
            response = getattr(top_level_session, method)(server)
        request = response.request
        spans = tracer.finished_spans()
        assert len(spans) == 2
        req_span, root_span = spans
        assert req_span.operation_name == 'requests.{}'.format(method)

        tags = req_span.tags
        assert tags['custom'] == 'tag'
        assert tags[ext_tags.COMPONENT] == 'requests'
        assert tags[ext_tags.SPAN_KIND] == ext_tags.SPAN_KIND_RPC_CLIENT
        assert tags[ext_tags.HTTP_STATUS_CODE] == 200
        assert tags[ext_tags.HTTP_METHOD] == method
        assert tags[ext_tags.HTTP_URL] == server
        assert ext_tags.ERROR not in tags

        assert request.headers['ot-tracer-spanid'] == '{0:x}'.format(req_span.context.span_id)
        assert request.headers['ot-tracer-traceid'] == '{0:x}'.format(req_span.context.trace_id)

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_successful_session_requests(self, tracer, session, method):
        with tracer.start_active_span('root'):
            getattr(session, method)(server)
        spans = tracer.finished_spans()
        assert len(spans) == 2

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_successful_requests(self, tracer, method):
        with tracer.start_active_span('root'):
            getattr(requests, method)(server)
        spans = tracer.finished_spans()
        assert len(spans) == 2
