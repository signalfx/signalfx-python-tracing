# Copyright (C) 2018-2019 SignalFx. All rights reserved.
import sys
import os

import pytest
import mock
import six

from signalfx_tracing.constants import (
    instrumented_attr,
    traceable_libraries,
    auto_instrumentable_libraries,
)
from signalfx_tracing.instrumentation import instrument, uninstrument, auto_instrument
from signalfx_tracing import utils

if six.PY2:
    from contextlib import nested
else:
    from contextlib import contextmanager, ExitStack

    @contextmanager
    def nested(*contexts):
        with ExitStack() as stack:
            for context in contexts:
                stack.enter_context(context)
            yield


expected_traceable_libraries = (
    "celery",
    "django",
    "elasticsearch",
    "falcon",
    "flask",
    "psycopg2",
    "pymongo",
    "pymysql",
    "redis",
    "requests",
    "tornado",
    "logging",
)
expected_auto_instrumentable_libraries = (
    "celery",
    "elasticsearch",
    "falcon",
    "flask",
    "psycopg2",
    "pymongo",
    "pymysql",
    "redis",
    "requests",
    "tornado",
    "logging",
)

tracing_enabled_env_var = "SIGNALFX_TRACING_ENABLED"


class TestInstrument(object):
    def test_traceable_libraries_contents(self):
        assert traceable_libraries == expected_traceable_libraries
        assert auto_instrumentable_libraries == expected_auto_instrumentable_libraries

    @pytest.fixture(autouse=True)
    def stubbed_instrumentor(self):
        """
        Allows us to stub instrumentor interfaces and target library manipulation.
        Without doing so, all instrumented libraries would need to be available
        in pytest context and this would effectively be a large e2e.
        """

        class Stub(object):  # Use a generic object for attribute loading
            pass

        module_store = {}  # Keep track of initial module state for teardown
        contexts = []  # mock.patch.object() contexts

        for library in expected_traceable_libraries:
            module = sys.modules.get(library)
            module_store[library] = module

            stubbed_module = Stub()
            stubbed_module.__spec__ = (
                mock.MagicMock()
            )  # needed for pkgutil.find_loader(library)
            sys.modules[library] = stubbed_module

            sfx_library = "signalfx_tracing.libraries.{}_".format(library)
            sfx_library_module = sys.modules.get(sfx_library)
            module_store[sfx_library] = sfx_library_module

            sfx_module = mock.MagicMock()
            sys.modules[sfx_library] = sfx_module

            # Ensure stubbed module references are immutable in closure patches
            def wrap_env(module_stub):
                def _instrument(tracer=None):
                    utils.mark_instrumented(module_stub)

                def _uninstrument():
                    utils.mark_uninstrumented(module_stub)

                contexts.append(
                    mock.patch.object(sfx_module, "instrument", _instrument)
                )
                contexts.append(
                    mock.patch.object(sfx_module, "uninstrument", _uninstrument)
                )

            wrap_env(stubbed_module)

        try:
            with nested(*contexts):
                yield
        finally:
            for library, module in module_store.items():
                if module:
                    sys.modules[library] = module
                else:
                    del sys.modules[library]

    def all_are_uninstrumented(self, modules):
        return all([not hasattr(module, instrumented_attr) for module in modules])

    @pytest.mark.parametrize("module_name", expected_traceable_libraries)
    def test_instrument_with_true_instruments_specified_libraries(self, module_name):
        mod = utils.get_module(module_name)
        assert not hasattr(mod, instrumented_attr)
        instrument(**{module_name: True})
        assert getattr(mod, instrumented_attr) is True

    @pytest.mark.parametrize("module_name", expected_traceable_libraries)
    def test_uninstrument_uninstruments_specified_libraries(self, module_name):
        instrument(**{module_name: True})
        mod = utils.get_module(module_name)
        assert getattr(mod, instrumented_attr) is True
        uninstrument(module_name)
        assert not hasattr(mod, instrumented_attr)

    @pytest.mark.parametrize("module_name", expected_traceable_libraries)
    def test_instrument_with_false_uninstruments_specified_libraries(self, module_name):
        instrument(**{module_name: True})
        mod = utils.get_module(module_name)
        assert getattr(mod, instrumented_attr) is True
        instrument(**{module_name: False})
        assert not hasattr(mod, instrumented_attr)

    @pytest.mark.parametrize("module_name", expected_traceable_libraries)
    def test_instrument_with_true_and_env_var_false_doesnt_instrument_specified_libraries(
        self, module_name
    ):
        env_var = "SIGNALFX_{0}_ENABLED".format(module_name.upper())
        os.environ[env_var] = "False"
        try:
            instrument(**{module_name: True})
            mod = utils.get_module(module_name)
            assert not hasattr(mod, instrumented_attr)
        finally:
            os.environ.pop(env_var)

    def test_auto_instrument_instruments_all_available_libraries(self):
        modules = [(utils.get_module(lib), lib) for lib in expected_traceable_libraries]
        assert self.all_are_uninstrumented(modules)

        auto_instrument()

        for module, library in modules:
            if library in expected_auto_instrumentable_libraries:
                assert getattr(module, instrumented_attr) is True
            else:
                assert not hasattr(module, instrumented_attr)

    @pytest.mark.parametrize(
        "env_var, are_uninstrumented", [("False", True), ("0", True), ("True", False)]
    )
    def test_env_var_disables_instrument(self, env_var, are_uninstrumented):
        os.environ[tracing_enabled_env_var] = env_var
        try:
            modules = [utils.get_module(lib) for lib in expected_traceable_libraries]
            assert self.all_are_uninstrumented(modules)

            for m in expected_traceable_libraries:
                instrument(**{m: True})

            assert self.all_are_uninstrumented(modules) is are_uninstrumented
        finally:
            os.environ.pop(tracing_enabled_env_var)

    @pytest.mark.parametrize(
        "env_var, are_uninstrumented", [("False", True), ("0", True), ("True", False)]
    )
    def test_env_var_disables_prevents_auto_instrument(
        self, env_var, are_uninstrumented
    ):
        os.environ[tracing_enabled_env_var] = env_var
        try:
            modules = [
                utils.get_module(lib) for lib in expected_auto_instrumentable_libraries
            ]
            assert self.all_are_uninstrumented(modules)

            auto_instrument()

            assert self.all_are_uninstrumented(modules) is are_uninstrumented
        finally:
            os.environ.pop(tracing_enabled_env_var)

    @pytest.mark.parametrize(
        "env_var, are_uninstrumented", [("False", True), ("0", True), ("True", False)]
    )
    def test_instrumentation_env_var_disabled_prevents_auto_instrument(
        self, env_var, are_uninstrumented
    ):
        enableds = [
            "SIGNALFX_{0}_ENABLED".format(lib.upper())
            for lib in expected_auto_instrumentable_libraries
        ]
        for enabled in enableds:
            os.environ[enabled] = env_var
        try:
            modules = [
                utils.get_module(lib) for lib in expected_auto_instrumentable_libraries
            ]
            assert self.all_are_uninstrumented(modules)

            auto_instrument()

            assert self.all_are_uninstrumented(modules) is are_uninstrumented
        finally:
            for enabled in enableds:
                os.environ.pop(enabled)
