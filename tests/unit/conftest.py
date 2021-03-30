from signalfx_tracing import tags as ext_tags


class SpanTest(object):
    def assert_span_contains_tags(self, span, tags):
        for k, v in tags.items():
            assert k in span.tags
            assert span.tags[k] == v

    def assert_span_with_exception(self, span, exc, min_tb_length=50):
        tags = span.tags
        assert tags[ext_tags.ERROR] is True
        assert tags[ext_tags.ERROR_MESSAGE] == str(exc)
        assert tags[ext_tags.ERROR_OBJECT] == str(exc.__class__)
        assert tags[ext_tags.ERROR_KIND] == exc.__class__.__name__
        tb = "".join(tags[ext_tags.ERROR_STACK])
        assert len(tb) >= min_tb_length
