# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
import sys
import os

import pytest
import mock
import six

from signalfx_tracing.constants import instrumented_attr, traceable_libraries, auto_instrumentable_libraries
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

expected_traceable_libraries = ('celery', 'django', 'elasticsearch', 'flask', 'psycopg2', 'pymongo', 'pymysql', 'redis',
                                'requests', 'tornado')
expected_auto_instrumentable_libraries = ('celery', 'elasticsearch', 'flask', 'psycopg2', 'pymongo', 'pymysql', 'redis',
                                          'requests', 'tornado')


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
            stubbed_module.__spec__ = mock.MagicMock()  # needed for pkgutil.find_loader(library)
            sys.modules[library] = stubbed_module

            sfx_library = 'signalfx_tracing.libraries.{}_'.format(library)
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

                contexts.append(mock.patch.object(sfx_module, 'instrument', _instrument))
                contexts.append(mock.patch.object(sfx_module, 'uninstrument', _uninstrument))

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

    def test_instrument_with_true_instruments_specified_libraries(self):
        tornado = utils.get_module('tornado')
        assert not hasattr(tornado, instrumented_attr)
        instrument(tornado=True)
        assert getattr(tornado, instrumented_attr) is True

    def test_uninstrument_uninstruments_specified_libraries(self):
        instrument(tornado=True)
        tornado = utils.get_module('tornado')
        assert getattr(tornado, instrumented_attr) is True
        uninstrument('tornado')
        assert not hasattr(tornado, instrumented_attr)

    def test_instrument_with_false_uninstruments_specified_libraries(self):
        instrument(tornado=True)
        tornado = utils.get_module('tornado')
        assert getattr(tornado, instrumented_attr) is True
        instrument(tornado=False)
        assert not hasattr(tornado, instrumented_attr)

    def test_auto_instrument_instruments_all_available_libraries(self):
        modules = [(utils.get_module(l), l) for l in expected_traceable_libraries]
        assert self.all_are_uninstrumented(modules)

        auto_instrument()

        for module, library in modules:
            if library in expected_auto_instrumentable_libraries:
                assert getattr(module, instrumented_attr) is True
            else:
                assert not hasattr(module, instrumented_attr)

    @pytest.mark.parametrize('env_var, are_uninstrumented', [('False', True), ('0', True), ('True', False)])
    def test_env_var_disables_instrument(self, env_var, are_uninstrumented):
        os.environ['SIGNALFX_TRACING_ENABLED'] = env_var
        modules = [utils.get_module(l) for l in expected_traceable_libraries]
        assert self.all_are_uninstrumented(modules)

        for m in expected_traceable_libraries:
            instrument(**{m: True})

        assert self.all_are_uninstrumented(modules) is are_uninstrumented

    @pytest.mark.parametrize('env_var, are_uninstrumented', [('False', True), ('0', True), ('True', False)])
    def test_env_var_disables_prevents_auto_instrument(self, env_var, are_uninstrumented):
        os.environ['SIGNALFX_TRACING_ENABLED'] = env_var
        modules = [utils.get_module(l) for l in expected_auto_instrumentable_libraries]
        assert self.all_are_uninstrumented(modules)

        auto_instrument()

        assert self.all_are_uninstrumented(modules) is are_uninstrumented
