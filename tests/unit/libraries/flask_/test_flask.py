# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from opentracing.mocktracer import MockTracer
from flask_opentracing import FlaskTracer
import opentracing
import pytest
import flask

from signalfx_tracing.libraries.flask_ import config, instrument, uninstrument
from .conftest import FlaskTestSuite


class TestFlaskConfig(FlaskTestSuite):

    @pytest.mark.parametrize('trace_all', (True, False))
    def test_instrument_flask_values_set_by_config(self, trace_all):
        tracer = MockTracer()
        config.tracer = tracer
        config.trace_all = trace_all
        # config.traced_attributes adoption is not exposed

        instrument()
        app = flask.Flask('MyFlaskApplication')

        flask_tracer = app.config['FLASK_TRACER']
        assert isinstance(flask_tracer, FlaskTracer)
        assert flask_tracer._tracer is tracer
        if trace_all:
            assert 'start_trace' in str(app.before_request_funcs.get(None))
            assert 'end_trace' in str(app.after_request_funcs.get(None))
        else:
            assert 'start_trace' not in str(app.before_request_funcs.get(None))
            assert 'end_trace' not in str(app.after_request_funcs.get(None))


class TestFlaskApplication(FlaskTestSuite):

    def make_app(self):
        app = flask.Flask('MyFlaskApplication')

        @app.route('/')
        def my_route():
            return 'Success!'

        return app

    def test_trace_with_default_config(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        instrument()
        app = self.make_app()

        flask_tracer = app.config['FLASK_TRACER']
        assert flask_tracer._tracer is tracer

        client = app.test_client()
        assert client.get('/').status_code == 200

        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.operation_name == 'my_route'
        assert span.tags == {'Extract failed': '', 'method': 'GET', 'path': '/'}

    def test_trace_with_specified_tracer_and_attributes(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.traced_attributes = ['url', 'blueprint', 'method']
        instrument()
        app = self.make_app()

        flask_tracer = app.config['FLASK_TRACER']
        assert flask_tracer._tracer is tracer

        client = app.test_client()
        assert client.get('/').status_code == 200

        spans = tracer.finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.operation_name == 'my_route'
        assert span.tags == {'Extract failed': '', 'method': 'GET',
                             'url': 'http://localhost/', 'blueprint': 'None'}

    def test_trace_without_trace_all(self):
        tracer = MockTracer()
        config.tracer = tracer
        config.trace_all = False
        instrument()
        app = self.make_app()

        flask_tracer = app.config['FLASK_TRACER']
        assert flask_tracer._tracer is tracer

        client = app.test_client()
        assert client.get('/').status_code == 200

        assert not tracer.finished_spans()

    def test_uninstrument_reverts_wrapper(self):
        tracer = MockTracer()
        opentracing.tracer = tracer
        instrument()
        app = self.make_app()

        client = app.test_client()
        assert client.get('/').status_code == 200

        assert len(tracer.finished_spans()) == 1

        tracer.reset()

        uninstrument()
        app = self.make_app()

        client = app.test_client()
        assert client.get('/').status_code == 200

        assert tracer.finished_spans() == []
