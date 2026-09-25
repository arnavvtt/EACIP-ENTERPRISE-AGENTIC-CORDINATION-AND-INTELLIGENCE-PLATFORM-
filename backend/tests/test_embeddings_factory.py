"""Tests for the embedding provider factory."""

import pytest

from app.config import settings
from app.embeddings import (
    MockEmbeddingProvider,
    get_embedding_provider,
)


def test_default_provider_is_mock(monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "mock")
    p = get_embedding_provider()
    assert isinstance(p, MockEmbeddingProvider)
    assert p.name == "mock"


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "unknown")
    with pytest.raises(ValueError):
        get_embedding_provider()


@pytest.mark.asyncio
async def test_mock_mode_needs_no_api_key(monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "mock")
    monkeypatch.setattr(settings, "voyage_api_key", "")
    p = get_embedding_provider()
    vectors, meta = await p.embed_batch(["test"])
    assert meta.dimensions == 1024
    assert len(vectors[0]) == 1024


def test_voyage_provider_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "voyage_api_key", "")
    from app.embeddings.base import EmbeddingError
    from app.embeddings.voyage_embedding_provider import (
        VoyageEmbeddingProvider,
    )
    with pytest.raises(EmbeddingError):
        VoyageEmbeddingProvider()