# Copyright (C) 2018 SignalFx. All rights reserved.
import os

from jaeger_client import Config, Tracer
import opentracing.span
import pytest
import mock

from signalfx_tracing import utils


token_var = "SIGNALFX_ACCESS_TOKEN"


class TestCreateTracer(object):
    @pytest.fixture(autouse=True)
    def reset_jaeger_environment(self):
        Config._initialized = False
        prev = {}
        for env_var in (
            "SIGNALFX_SERVICE_NAME",
            token_var,
            "SIGNALFX_ENDPOINT_URL",
            "SIGNALFX_SAMPLER_TYPE",
            "SIGNALFX_SAMPLER_PARAM",
            "SIGNALFX_PROPAGATION",
        ):
            try:
                prev[env_var] = os.environ.pop(env_var)
            except KeyError:
                pass
        yield
        for env_var in prev:
            if prev[env_var] is not None:
                os.environ[env_var] = prev[env_var]

    @pytest.fixture(autouse=True)
    def reset_cached_tracer(self):
        prev = utils._tracer
        utils._tracer = None
        yield
        utils._tracer = prev

    def test_access_token_optional(self):
        utils.create_tracer()

    def test_creation_with_access_token_arg(self):
        tracer = utils.create_tracer("AccessToken")
        assert isinstance(tracer, Tracer)

    def test_creation_is_idempotent(self):
        tracer = utils.create_tracer("AccessToken")
        assert isinstance(tracer, Tracer)
        assert utils.create_tracer("SomethingElse") is tracer

    def test_creation_allows_multiple(self):
        tracer = utils.create_tracer("AccessToken")
        assert isinstance(tracer, Tracer)

        other = utils.create_tracer("SomethingElse", allow_multiple=True)
        assert isinstance(other, Tracer)
        assert other is not tracer

        assert utils.create_tracer("SomethingElse") is other

    def test_creation_with_access_token_env_var(self):
        os.environ[token_var] = "AccessToken"
        tracer = utils.create_tracer()
        assert isinstance(tracer, Tracer)

    def test_has_start_active_span(self):
        tracer = utils.create_tracer()
        assert isinstance(
            tracer.start_active_span("test_span").span, opentracing.span.Span
        )

    def test_defaults(self):
        with mock.patch("jaeger_client.Config") as cfg:
            utils.create_tracer("auth_token")
        created = cfg.call_args[0][0]
        assert created["service_name"] == "SignalFx-Tracing"
        assert created["jaeger_user"] == "auth"
        assert created["jaeger_password"] == "auth_token"
        assert created["jaeger_endpoint"] == "http://localhost:9080/v1/trace"
        assert created["propagation"] == "b3"

    def test_defaults_overridden_by_config(self):
        config = dict(
            service_name="SomeService",
            jaeger_user="SomeUser",
            jaeger_password="SomePassword",
            jaeger_endpoint="SomeEndpoint",
            propagation="SomePropagation",
        )

        with mock.patch("jaeger_client.Config") as cfg:
            utils.create_tracer("auth_token", config=config)
        created = cfg.call_args[0][0]
        assert created["service_name"] == "SomeService"
        assert created["jaeger_user"] == "SomeUser"
        assert created["jaeger_password"] == "SomePassword"
        assert created["jaeger_endpoint"] == "SomeEndpoint"
        assert created["propagation"] == "SomePropagation"

    def test_defaults_overridden_by_kwargs(self):
        config = dict(
            jaeger_user="SomeUser",
            jaeger_password="SomePassword",
            jaeger_endpoint="SomeEndpoint",
            propagation="SomePropagation",
        )

        with mock.patch("jaeger_client.Config") as cfg:
            utils.create_tracer("auth_token", config=config, service_name="SomeService")
        created = cfg.call_args[0][0]
        assert created["jaeger_user"] == "SomeUser"
        assert created["jaeger_password"] == "SomePassword"
        assert created["jaeger_endpoint"] == "SomeEndpoint"
        assert created["propagation"] == "SomePropagation"
        kwargs = cfg.call_args[1]
        assert kwargs["service_name"] == "SomeService"

    def test_defaults_overridden_by_env_vars(self):
        env = os.environ
        env["SIGNALFX_SERVICE_NAME"] = "SomeService"
        env[token_var] = "SomeToken"
        env["SIGNALFX_ENDPOINT_URL"] = "SomeEndpoint"
        env["SIGNALFX_SAMPLER_TYPE"] = "probabilistic"
        env["SIGNALFX_SAMPLER_PARAM"] = ".05"
        env["SIGNALFX_PROPAGATION"] = "SomePropagation"

        with mock.patch("jaeger_client.Config") as cfg:
            utils.create_tracer()
        created = cfg.call_args[0][0]
        assert created["service_name"] == "SomeService"
        assert created["jaeger_user"] == "auth"
        assert created["jaeger_password"] == "SomeToken"
        assert created["jaeger_endpoint"] == "SomeEndpoint"
        assert created["sampler"]["type"] == "probabilistic"
        assert created["sampler"]["param"] == 0.05
        assert created["propagation"] == "SomePropagation"

    def test_defaults_overridden_by_empty_env_vars(self):
        env = os.environ
        env["SIGNALFX_SERVICE_NAME"] = ""
        env[token_var] = ""
        env["SIGNALFX_ENDPOINT_URL"] = ""
        env["SIGNALFX_SAMPLER_TYPE"] = ""
        env["SIGNALFX_SAMPLER_PARAM"] = ""
        env["SIGNALFX_PROPAGATION"] = ""

        with mock.patch("jaeger_client.Config") as cfg:
            utils.create_tracer()
        created = cfg.call_args[0][0]
        assert created["service_name"] == ""
        assert created["jaeger_user"] == "auth"
        assert created["jaeger_password"] == ""
        assert created["jaeger_endpoint"] == ""
        assert created["sampler"]["type"] == ""
        assert created["sampler"]["param"] == ""
        assert created["propagation"] == ""

    @pytest.mark.parametrize(
        "sampler, param, expected",
        (("const", "0", 0), ("const", "1", 1), ("probabilistic", ".1", 0.1)),
    )
    def test_sampler_by_env_var(self, sampler, param, expected):
        os.environ["SIGNALFX_SAMPLER_TYPE"] = sampler
        os.environ["SIGNALFX_SAMPLER_PARAM"] = param

        with mock.patch("jaeger_client.Config") as cfg:
            utils.create_tracer()
        created = cfg.call_args[0][0]
        assert created["sampler"]["type"] == sampler
        assert created["sampler"]["param"] == expected

    def test_create_tracer_sanity(self):
        tracer = utils.create_tracer()
        tracer.close()
