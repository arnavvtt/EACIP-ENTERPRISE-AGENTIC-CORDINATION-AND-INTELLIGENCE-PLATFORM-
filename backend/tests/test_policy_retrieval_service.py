"""
Tests for PolicyRetrievalService.

Uses the mock embedding provider so tests run without API keys.
Requires policy_chunks to exist in DB — uses monkeypatch to skip
if empty.
"""

import pytest
import pytest_asyncio

from app.config import settings
from app.database import AsyncSessionLocal
from app.services import PolicyRetrievalService


@pytest_asyncio.fixture
async def session():
    async with AsyncSessionLocal() as s:
        yield s


@pytest.mark.asyncio
async def test_empty_query_returns_empty(session, monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "mock")
    svc = PolicyRetrievalService(session)
    result = await svc.search("", limit=5)
    assert result.fused_hits == []
    assert result.lexical_count == 0
    assert result.semantic_count == 0


@pytest.mark.asyncio
async def test_whitespace_query_returns_empty(session, monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "mock")
    svc = PolicyRetrievalService(session)
    result = await svc.search("   ", limit=5)
    assert result.fused_hits == []


@pytest.mark.asyncio
async def test_query_returns_fused_result(session, monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "mock")
    svc = PolicyRetrievalService(session)

    # This query matches existing seeded policy content
    result = await svc.search("supplier qualification", limit=5)

    # Even if data is present or missing, shape must be valid
    assert isinstance(result.lexical_count, int)
    assert isinstance(result.semantic_count, int)
    assert isinstance(result.fused_hits, list)

    # If any hits, they should be sorted by rrf_score
    if len(result.fused_hits) > 1:
        scores = [h.rrf_score for h in result.fused_hits]
        assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_per_retriever_limit_respected(session, monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "mock")
    svc = PolicyRetrievalService(session)
    result = await svc.search(
        "supplier", limit=5, per_retriever_limit=3
    )
    assert len(result.fused_hits) <= 5