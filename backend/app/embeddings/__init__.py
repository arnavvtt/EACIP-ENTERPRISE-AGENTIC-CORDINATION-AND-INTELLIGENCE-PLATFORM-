"""
Embedding layer.

Public API:
- EmbeddingProvider        : abstract interface
- EmbeddingResponse        : metadata for a batch
- MockEmbeddingProvider    : deterministic stub (tests/dev)
- get_embedding_provider() : factory based on settings
- EmbeddingError           : base exception
- EMBEDDING_DIMENSIONS     : fixed dimension (1024)
"""

from app.embeddings.base import (
    EMBEDDING_DIMENSIONS,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingResponse,
)
from app.embeddings.factory import get_embedding_provider
from app.embeddings.mock_provider import MockEmbeddingProvider

__all__ = [
    "EMBEDDING_DIMENSIONS",
    "EmbeddingError",
    "EmbeddingProvider",
    "EmbeddingResponse",
    "MockEmbeddingProvider",
    "get_embedding_provider",
]