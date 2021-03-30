# Copyright (C) 2018 SignalFx. All rights reserved.
import pytest

from opentracing.mocktracer import MockTracer
import opentracing

from signalfx_tracing.utils import trace
from signalfx_tracing import tags as ext_tags

from .conftest import SpanTest


class DecoratorTest(SpanTest):
    @pytest.fixture(autouse=True)
    def _setup_tracer(self):
        self.tracer = MockTracer()
        opentracing.tracer = self.tracer


class TestFunctionDecorator(DecoratorTest):
    def test_unused_decorator(self):
        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            return 123

        assert self.tracer.finished_spans() == []
        assert traced_function.__name__ == "traced_function"

    def test_basic_decorator(self):
        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            return 123

        assert traced_function(1, one=1) == 123
        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "traced_function"
        assert spans[0].tags == dict()

        assert traced_function.__name__ == "traced_function"

    def test_named_decorator(self):
        @trace("operation_name")
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            return 123

        assert traced_function(1, one=1) == 123
        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"
        assert spans[0].tags == dict()
        assert traced_function.__name__ == "traced_function"

    def test_tagged_decorator(self):
        @trace(tags=dict(one=1, two="2"))
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            return 123

        assert traced_function(1, one=1) == 123
        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "traced_function"
        assert spans[0].tags == dict(one=1, two="2")

        assert traced_function.__name__ == "traced_function"

    def test_named_and_tagged_decorator(self):
        @trace("operation_name", tags=dict(one=1, two="2"))
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            return 123

        assert traced_function(1, one=1) == 123
        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"
        assert spans[0].tags == dict(one=1, two="2")

        assert traced_function.__name__ == "traced_function"

    def test_positional_named_and_tagged_decorator(self):
        @trace("operation_name", dict(one=1, two="2"))
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            return 123

        assert traced_function(1, one=1) == 123
        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"
        assert spans[0].tags == dict(one=1, two="2")

        assert traced_function.__name__ == "traced_function"

    def test_errored_function(self):
        class CustomException(Exception):
            pass

        error = CustomException("SomeException")

        @trace
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            raise error

        with pytest.raises(CustomException):
            traced_function(1, one=1)

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "traced_function"
        self.assert_span_with_exception(spans[0], error)

        assert traced_function.__name__ == "traced_function"

    def test_named_and_tagged_errored_function(self):
        class CustomException(Exception):
            pass

        error = CustomException("SomeException")

        @trace("operation_name", tags=dict(one=1, two="2"))
        def traced_function(*args, **kwargs):
            assert args == (1,)
            assert kwargs == dict(one=1)
            raise error

        with pytest.raises(CustomException):
            traced_function(1, one=1)

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"

        self.assert_span_contains_tags(
            spans[0],
            {
                "one": 1,
                "two": "2",
            },
        )
        self.assert_span_with_exception(spans[0], error)


class TestMethodDecorator(DecoratorTest):
    def test_named_and_tagged_errored_method(self):
        class CustomException(Exception):
            pass

        error = CustomException("SomeException")

        class Thing(object):
            @trace("operation_name", tags=dict(one=1, two="2"))
            def traced_method(self, *args, **kwargs):
                assert args == (1,)
                assert kwargs == dict(one=1)
                raise error

        with pytest.raises(CustomException):
            Thing().traced_method(1, one=1)

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"

        self.assert_span_contains_tags(
            spans[0],
            {
                "one": 1,
                "two": "2",
            },
        )
        self.assert_span_with_exception(spans[0], error)

        assert Thing().traced_method.__name__ == "traced_method"

    def test_named_and_tagged_errored_classmethod(self):
        class CustomException(Exception):
            pass

        error = CustomException("AnotherException")

        class Thing(object):
            @classmethod
            @trace("operation_name", tags=dict(one=1, two="2"))
            def traced_method(cls, *args, **kwargs):
                assert args == (1,)
                assert kwargs == dict(one=1)
                raise error

        with pytest.raises(CustomException):
            Thing().traced_method(1, one=1)

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"
        self.assert_span_contains_tags(
            spans[0], {"one": 1, "two": "2", ext_tags.ERROR: True}
        )
        self.assert_span_with_exception(spans[0], error)

        assert Thing().traced_method.__name__ == "traced_method"

    def test_named_and_tagged_errored_staticmethod(self):
        class CustomException(Exception):
            pass

        error = CustomException("YetAnotherException")

        class Thing(object):
            @staticmethod
            @trace("operation_name", tags=dict(one=1, two="2"))
            def traced_method(*args, **kwargs):
                assert args == (1,)
                assert kwargs == dict(one=1)
                raise error

        with pytest.raises(CustomException):
            Thing.traced_method(1, one=1)

        spans = self.tracer.finished_spans()
        assert len(spans) == 1
        assert spans[0].operation_name == "operation_name"
        self.assert_span_contains_tags(spans[0], {"one": 1, "two": "2"})
        self.assert_span_with_exception(spans[0], error)

        assert Thing().traced_method.__name__ == "traced_method"
