# Copyright (C) 2018 SignalFx. All rights reserved.
import sys

from opentracing.mocktracer import MockTracer
from wrapt import wrap_function_wrapper
import opentracing
import pytest

from signalfx_tracing import utils, constants


def test_get_module_imports_unimported_modules():
    restore_logging = False
    if "logging" in sys.modules:
        restore_logging = True
        del sys.modules["logging"]
    try:
        logging = utils.get_module("logging")
        assert logging == sys.modules["logging"]
    finally:
        if restore_logging:
            import logging


def test_get_module_is_none_for_unavailable_modules():
    assert utils.get_module("not_a_real_module_12345") is None


def test_mark_instrumented_and_uninstrumented():
    class MockModule(object):
        pass

    module = MockModule()
    utils.mark_instrumented(module)
    assert getattr(module, constants.instrumented_attr) is True
    assert utils.is_instrumented(module) is True
    utils.mark_uninstrumented(module)
    assert not hasattr(module, constants.instrumented_attr)
    assert utils.is_instrumented(module) is False


def test_empty_config():
    cfg = utils.Config()
    cfg.thing = 123
    assert cfg["thing"] == 123
    assert cfg.thing == 123
    del cfg.thing
    with pytest.raises(KeyError):
        cfg["thing"]
    with pytest.raises(AttributeError):
        cfg.thing


def test_config_with_kwargs():
    two = dict(three=3)
    cfg = utils.Config(one=1, two=two)
    assert cfg["one"] == 1
    assert cfg.one == 1
    assert cfg["two"] == two
    assert cfg.two == two
    cfg.one = "one"
    assert cfg["one"] == "one"
    assert cfg.one == "one"


def test_revert_wrapper():
    class Namespace:
        def wrappee(self, *args, **kwargs):
            return "wrappee"

    def wrapper(self, *args, **kwargs):
        return "wrapper"

    wrap_function_wrapper(Namespace, "wrappee", wrapper)
    assert Namespace().wrappee() == "wrapper"

    utils.revert_wrapper(Namespace, "wrappee")
    assert Namespace().wrappee() == "wrappee"


def test_is_truthy():
    for val in (
        False,
        None,
        0,
        [],
        (),
        {},
        set(),
        "FaLsE",
        "f",
        "F",
        "No",
        "n",
        "N",
        "",
        b"",
    ):
        assert utils.is_truthy(val) is False

    for val in (True, "y", 1, "asdf", [1], (1,), {"one": 1}, set([1])):
        assert utils.is_truthy(val) is True


def test_tracer_proxy():
    proxy = utils.TracerProxy()
    assert proxy == opentracing.tracer
    assert proxy.start_active_span == opentracing.tracer.start_active_span

    mock = MockTracer()
    proxy.set_tracer(mock)
    assert proxy == mock
    assert proxy.start_active_span == mock.start_active_span
