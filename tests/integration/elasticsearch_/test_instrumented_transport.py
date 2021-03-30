# Copyright (C) 2019 SignalFx. All rights reserved.
from time import sleep

from opentracing.mocktracer import MockTracer
import elasticsearch
import docker
import pytest

from signalfx_tracing.libraries import elasticsearch_config
from signalfx_tracing import instrument, uninstrument
from tests.utils import random_int


@pytest.fixture(scope="session")
def elasticsearch_container(request):
    es_version = request.config.getoption("--elasticsearch-image-version", "6.5.4")
    docker_client = docker.from_env()
    es_container = docker_client.containers.run(
        "elasticsearch:{}".format(es_version), ports={"9200/tcp": 9200}, detach=True
    )
    try:
        es_client = elasticsearch.Elasticsearch()
        for i in range(60):
            try:
                if es_client.ping():
                    break
            except elasticsearch.ConnectionError:
                pass

            if i == 59:
                raise RuntimeError("Failed to connect to Elasticsearch.")
            sleep(0.5)

        yield es_container
    finally:
        es_container.remove(v=True, force=True)


class TestElasticsearch(object):
    @pytest.fixture
    def tracer(self, elasticsearch_container):
        yield MockTracer()

    @pytest.fixture
    def instrumented_elasticsearch(self, tracer):
        elasticsearch_config.prefix = "MyPrefix"
        yield instrument(tracer, elasticsearch=True)
        uninstrument("elasticsearch")

    @pytest.fixture
    def tracer_and_elasticsearch(self, tracer):
        return tracer, elasticsearch.Elasticsearch()

    @pytest.fixture
    def tracer_and_elasticsearch_transport(self, tracer):
        return tracer, elasticsearch.Elasticsearch(transport=elasticsearch.Transport)

    @pytest.fixture
    def tracer_and_elasticsearch_transport_transport(self, tracer):
        import elasticsearch.transport  # must be imported after auto-instrumentation

        return tracer, elasticsearch.Elasticsearch(
            transport=elasticsearch.transport.Transport
        )

    @pytest.fixture(
        params=(
            "tracer_and_elasticsearch",
            "tracer_and_elasticsearch_transport",
            "tracer_and_elasticsearch_transport_transport",
        )
    )
    def tracer_and_client(self, request, instrumented_elasticsearch):
        yield request.getfixturevalue(request.param)

    @pytest.fixture(
        params=(
            "tracer_and_elasticsearch",
            "tracer_and_elasticsearch_transport",
            "tracer_and_elasticsearch_transport_transport",
        )
    )
    def tracer_and_uninstrumented_client(self, request):
        uninstrument("elasticsearch")
        yield request.getfixturevalue(request.param)

    def test_uninstrumented_not_traced(
        self, instrumented_elasticsearch, tracer_and_uninstrumented_client
    ):
        tracer, es = tracer_and_uninstrumented_client

        doc_id = random_int(0)
        body = dict(lorem="ipsum" * 1024)
        index = es.index(
            index="some-index",
            doc_type="some-doc-type",
            id=doc_id,
            body=body,
            params={"refresh": "true"},
        )
        doc_id = str(doc_id)
        assert index["_id"] == doc_id
        assert index.get("result") == "created" or index.get("created")
        lorem = es.get(index="some-index", doc_type="some-doc-type", id=doc_id)
        assert lorem["_id"] == doc_id
        assert lorem["_source"] == body

        assert not tracer.finished_spans()

    def test_add_and_get_document(self, tracer_and_client):
        tracer, es = tracer_and_client

        doc_id = random_int(0)
        body = dict(lorem="ipsum" * 1024)
        index = es.index(
            index="some-index",
            doc_type="some-doc-type",
            id=doc_id,
            body=body,
            params={"refresh": "true"},
        )
        doc_id = str(doc_id)
        assert index["_id"] == doc_id
        assert index.get("result") == "created" or index.get("created")
        lorem = es.get(index="some-index", doc_type="some-doc-type", id=doc_id)
        assert lorem["_id"] == doc_id
        assert lorem["_source"] == body

        spans = tracer.finished_spans()
        assert len(spans) == 2
        expected_url = "/some-index/some-doc-type/{}".format(doc_id)
        for span in spans:
            assert span.operation_name == "MyPrefix{}".format(expected_url)
            assert span.tags["elasticsearch.url"] == expected_url
            assert span.tags["component"] == "elasticsearch-py"
