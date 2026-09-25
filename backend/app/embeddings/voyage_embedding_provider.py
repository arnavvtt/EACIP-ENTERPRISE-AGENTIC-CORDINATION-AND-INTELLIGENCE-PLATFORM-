"""
Voyage AI embedding provider.

Provider abstraction for Voyage AI's embeddings API.

Requirements:
- VOYAGE_API_KEY set in environment
- httpx installed (already present in EACIP)

Default model: voyage-4-lite (1024-dim, retrieval-focused)
Other models:  voyage-3, voyage-3-lite, voyage-4

Notes:
- Voyage supports asymmetric retrieval via input_type:
    * "document" for policy chunks (ingestion)
    * "query"    for user queries (retrieval)
- No latency assumptions; actual timing is measured per call.
- Voyage rate limits/quotas are external; provider surfaces errors
  as EmbeddingError.
- Changing the model may require re-embedding stored documents.
"""

import time

import httpx

from app.config import settings
from app.embeddings.base import (
    EMBEDDING_DIMENSIONS,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingResponse,
)


class VoyageEmbeddingProvider(EmbeddingProvider):
    """Real embedding provider using Voyage AI."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self._api_key = api_key or settings.voyage_api_key
        self._model = model or settings.embedding_model
        self._base_url = (
            base_url or settings.voyage_base_url
        ).rstrip("/")

        if not self._api_key:
            raise EmbeddingError(
                "Voyage API key is not set. "
                "Configure VOYAGE_API_KEY in .env."
            )

    @property
    def name(self) -> str:
        return "voyage"

    @property
    def model(self) -> str:
        return self._model

    async def embed_batch(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> tuple[list[list[float]], EmbeddingResponse]:
        """
        Embed a batch of texts.

        Args:
            texts: List of strings to embed
            input_type: "document" for chunks, "query" for search queries
        """
        if not texts:
            meta = EmbeddingResponse(
                provider=self.name,
                model=self.model,
                dimensions=EMBEDDING_DIMENSIONS,
                count=0,
                latency_ms=0.0,
            )
            return [], meta

        start = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "input": texts,
                        "input_type": input_type,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as e:
            raise EmbeddingError(
                f"Voyage HTTP {e.response.status_code}: "
                f"{e.response.text[:200]}"
            ) from e
        except httpx.HTTPError as e:
            raise EmbeddingError(
                f"Voyage request failed: {e}"
            ) from e
        except Exception as e:
            raise EmbeddingError(
                f"Voyage unexpected error: {e}"
            ) from e

        data = payload.get("data") or []
        if not data:
            raise EmbeddingError("Voyage returned no embeddings.")

        # Sort by index for order safety
        data = sorted(data, key=lambda item: item.get("index", 0))

        vectors: list[list[float]] = []
        for item in data:
            values = list(item.get("embedding") or [])
            if len(values) != EMBEDDING_DIMENSIONS:
                raise EmbeddingError(
                    f"Voyage returned {len(values)} dims, "
                    f"expected {EMBEDDING_DIMENSIONS}."
                )
            vectors.append(values)

        if len(vectors) != len(texts):
            raise EmbeddingError(
                f"Voyage returned {len(vectors)} vectors for "
                f"{len(texts)} inputs."
            )

        latency_ms = (time.perf_counter() - start) * 1000

        meta = EmbeddingResponse(
            provider=self.name,
            model=self.model,
            dimensions=EMBEDDING_DIMENSIONS,
            count=len(texts),
            latency_ms=latency_ms,
        )
        return vectors, meta