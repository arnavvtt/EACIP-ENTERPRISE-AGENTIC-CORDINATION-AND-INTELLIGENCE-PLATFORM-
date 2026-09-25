"""
Mock embedding provider — deterministic, no API calls.

Purpose:
- Unit tests
- CI pipelines
- Local development when external API access is not required

IMPORTANT:
- Mock is NOT semantic intelligence. It produces reproducible vectors
  for pipeline testing. Retrieval quality with mock is meaningless.
- Same input → same vector, always.
- Generates 1024-dim vectors directly (no padding).
- input_type is accepted but ignored (mock has no semantic model).
"""

import hashlib
import math
import time

from app.embeddings.base import (
    EMBEDDING_DIMENSIONS,
    EmbeddingProvider,
    EmbeddingResponse,
)


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic, offline embedding provider."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return "mock-v1"

    async def embed_batch(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> tuple[list[list[float]], EmbeddingResponse]:
        start = time.perf_counter()
        vectors = [self._vector(t) for t in texts]
        latency_ms = (time.perf_counter() - start) * 1000

        meta = EmbeddingResponse(
            provider=self.name,
            model=self.model,
            dimensions=EMBEDDING_DIMENSIONS,
            count=len(texts),
            latency_ms=latency_ms,
        )
        return vectors, meta

    @staticmethod
    def _vector(text: str) -> list[float]:
        seed = hashlib.sha256((text or "").encode("utf-8")).digest()
        values: list[float] = []
        counter = 0
        while len(values) < EMBEDDING_DIMENSIONS:
            block = hashlib.sha256(
                seed + counter.to_bytes(4, "big")
            ).digest()
            for b in block:
                values.append(b / 255.0 - 0.5)
                if len(values) >= EMBEDDING_DIMENSIONS:
                    break
            counter += 1

        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]