"""Tests for MockEmbeddingProvider."""

import math

import pytest

from app.embeddings import (
    EMBEDDING_DIMENSIONS,
    MockEmbeddingProvider,
)


@pytest.mark.asyncio
async def test_dimensions_are_1024():
    p = MockEmbeddingProvider()
    vectors, meta = await p.embed_batch(["hello"])
    assert meta.dimensions == 1024
    assert len(vectors) == 1
    assert len(vectors[0]) == EMBEDDING_DIMENSIONS
    assert EMBEDDING_DIMENSIONS == 1024


@pytest.mark.asyncio
async def test_deterministic():
    p = MockEmbeddingProvider()
    v1, _ = await p.embed_batch(["hello world"])
    v2, _ = await p.embed_batch(["hello world"])
    assert v1 == v2


@pytest.mark.asyncio
async def test_different_inputs_differ():
    p = MockEmbeddingProvider()
    v1, _ = await p.embed_batch(["hello"])
    v2, _ = await p.embed_batch(["world"])
    assert v1 != v2


@pytest.mark.asyncio
async def test_batch_preserves_order():
    p = MockEmbeddingProvider()
    inputs = ["a", "b", "c"]
    vectors, meta = await p.embed_batch(inputs)
    assert meta.count == 3
    singles = [((await p.embed_batch([t]))[0])[0] for t in inputs]
    assert vectors == singles


@pytest.mark.asyncio
async def test_vector_is_normalized():
    p = MockEmbeddingProvider()
    vectors, _ = await p.embed_batch(["hello"])
    norm = math.sqrt(sum(x * x for x in vectors[0]))
    assert abs(norm - 1.0) < 1e-6


@pytest.mark.asyncio
async def test_metadata_fields():
    p = MockEmbeddingProvider()
    _, meta = await p.embed_batch(["a", "b"])
    assert meta.provider == "mock"
    assert meta.model == "mock-v1"
    assert meta.count == 2
    assert meta.dimensions == 1024
    assert meta.latency_ms >= 0.0


@pytest.mark.asyncio
async def test_empty_input_string():
    p = MockEmbeddingProvider()
    vectors, meta = await p.embed_batch([""])
    assert meta.count == 1
    assert len(vectors[0]) == EMBEDDING_DIMENSIONS