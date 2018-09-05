# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import sys

import pytest
import mock

from signalfx_tracing.constants import instrumented_attr, traceable_libraries
from signalfx_tracing.instrumentation import instrument, uninstrument, auto_instrument
from signalfx_tracing import utils


expected_libraries = ('django',)


class TestInstrument(object):

    def test_traceable_libraries_contents(self):
        assert traceable_libraries == expected_libraries

    @pytest.fixture
    def stubbed_instrumenter(self):
        """
        Allows us to stub instrumenter interface and target library manipulation.
        Without doing so, all instrumented libraries would need to be available
        in pytest context and this would effectively be a large e2e.
        TODO: make generic for all expected_libraries as more are added.
        """
        class Mock(object):
            pass

        django_lib = sys.modules.get('django')
        django = Mock()  # Use a generic Mock for attribute loading
        django.__spec__ = mock.MagicMock()  # needed for pkgutil.find_loader(library)
        sys.modules['django'] = django

        sfx_django_lib = sys.modules.get('signalfx_tracing.libraries.django_')
        sfx_django = mock.MagicMock()
        sys.modules['signalfx_tracing.libraries.django_'] = sfx_django

        def _instrument(tracer=None):
            utils.mark_instrumented(django)

        def _uninstrument():
            utils.mark_uninstrumented(django)

        try:
            with mock.patch.object(sfx_django, 'instrument', _instrument):
                with mock.patch.object(sfx_django, 'uninstrument', _uninstrument):
                    yield
        finally:
            if django_lib:
                sys.modules['django'] = django_lib
            else:
                del sys.modules['django']
            if sfx_django_lib:
                sys.modules['signalfx_tracing.libraries.django_'] = sfx_django_lib
            else:
                del sys.modules['signalfx_tracing.libraries.django_']

    def test_instrument_with_true_instruments_specified_libraries(self, stubbed_instrumenter):
        django = utils.get_module('django')
        assert not hasattr(django, instrumented_attr)
        instrument(django=True)
        assert getattr(django, instrumented_attr) is True

    def test_uninstrument_uninstruments_specified_libraries(self, stubbed_instrumenter):
        instrument(django=True)
        django = utils.get_module('django')
        assert getattr(django, instrumented_attr) is True
        uninstrument('django')
        assert not hasattr(django, instrumented_attr)

    def test_instrument_with_false_uninstruments_specified_libraries(self, stubbed_instrumenter):
        instrument(django=True)
        django = utils.get_module('django')
        assert getattr(django, instrumented_attr) is True
        instrument(django=False)
        assert not hasattr(django, instrumented_attr)

    def test_auto_instrument_instruments_all_available_libraries(self, stubbed_instrumenter):
        modules = [utils.get_module(l) for l in expected_libraries]
        for module in modules:
            assert not hasattr(module, instrumented_attr)

        auto_instrument()

        for module in modules:
            assert getattr(module, instrumented_attr) is True
