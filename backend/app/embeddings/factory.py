"""
Embedding provider factory.

Reads settings.embedding_provider and returns the appropriate instance.
- "mock"   → MockEmbeddingProvider (default, no API calls)
- "voyage" → VoyageEmbeddingProvider (requires VOYAGE_API_KEY)
"""

from app.config import settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.mock_provider import MockEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider instance."""
    provider = settings.embedding_provider.lower().strip()

    if provider == "mock":
        return MockEmbeddingProvider()

    if provider == "voyage":
        from app.embeddings.voyage_embedding_provider import (
            VoyageEmbeddingProvider,
        )
        return VoyageEmbeddingProvider()

    raise ValueError(
        f"Unknown embedding provider: '{provider}'. "
        f"Available: 'mock', 'voyage'."
    )