# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import os

from jaeger_client import Config, Tracer
import pytest

from signalfx_tracing import utils


env_var = 'SIGNALFX_ACCESS_TOKEN'


class TestCreateTracer(object):

    @pytest.fixture(autouse=True)
    def reset_jaeger_environment(self):
        Config._initialized = False
        prev = None
        try:
            prev = os.environ.pop(env_var)
        except KeyError:
            pass
        yield
        if prev is not None:
            os.environ[env_var] = prev

    def test_creation_requires_access_token(self):
        with pytest.raises(ValueError):
            utils.create_tracer()

    def test_creation_with_access_token_arg(self):
        tracer = utils.create_tracer('AccessToken')
        assert isinstance(tracer, Tracer)

    def test_creation_with_access_token_env_var(self):
        os.environ[env_var] = 'AccessToken'
        tracer = utils.create_tracer()
        assert isinstance(tracer, Tracer)

    def test_access_token_provided_to_sender(self):
        tracer = utils.create_tracer('auth_token')
        assert tracer.reporter._sender.user == 'auth'
        assert tracer.reporter._sender.password == 'auth_token'
        assert tracer.reporter._sender.url == 'https://ingest.signalfx.com/v1/trace'

    def test_defaults_overridden_by_config(self):
        config = dict(service_name='SomeService',
                      jaeger_user='SomeUser',
                      jaeger_password='SomePassword',
                      jaeger_endpoint='SomeEndpoint')
        tracer = utils.create_tracer('auth_token', config=config)
        assert tracer.reporter._sender.user == 'SomeUser'
        assert tracer.reporter._sender.password == 'SomePassword'
        assert tracer.reporter._sender.url == 'SomeEndpoint'
