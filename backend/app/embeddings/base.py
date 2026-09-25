"""
Embedding provider abstraction.

Same architectural pattern as LLMProvider (Stage 4):
- interface + multiple providers + factory
- caller depends only on the interface

Design notes:
- Fixed dimension (1024) across all providers so a single pgvector
  column can store vectors from any provider. This is a DELIBERATE
  SCHEMA choice.

- IMPORTANT — provider/model mixing:
    Same dimensionality provides schema compatibility, but vectors
    from DIFFERENT providers or models must NOT be mixed in the same
    active similarity index. Vector spaces are not comparable across
    models. If provider or model changes, existing stored documents
    MUST be re-embedded.

- Mock provider is a deterministic stub — it is NOT real semantic
  intelligence and must not be treated as such.

- Latency of any provider is NOT assumed; the response object carries
  timing so we can measure later.

- input_type is passed through to providers that support asymmetric
  retrieval (e.g., Voyage). Providers that don't support it can ignore
  the parameter.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


EMBEDDING_DIMENSIONS = 1024


@dataclass
class EmbeddingResponse:
    """Metadata returned alongside a batch of embeddings."""

    provider: str
    model: str
    dimensions: int
    count: int
    latency_ms: float


class EmbeddingError(Exception):
    """Raised on any embedding failure."""
    pass


class EmbeddingProvider(ABC):
    """Abstract base for all embedding providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        ...

    @property
    def dimensions(self) -> int:
        return EMBEDDING_DIMENSIONS

    @abstractmethod
    async def embed_batch(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> tuple[list[list[float]], EmbeddingResponse]:
        ...

    async def embed_one(
        self,
        text: str,
        input_type: str = "document",
    ) -> tuple[list[float], EmbeddingResponse]:
        vectors, meta = await self.embed_batch([text], input_type=input_type)
        return vectors[0], meta