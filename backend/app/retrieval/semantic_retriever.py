"""
Semantic retriever — Voyage embeddings + pgvector cosine similarity.

Query flow:
    1. Embed query via Voyage (input_type="query")
    2. Search pgvector using cosine distance (<=>)
    3. Convert cosine distance → cosine similarity
    4. Return top-K SemanticHit

Design:
- Read-only.
- Uses pgvector's native `<=>` cosine distance operator.
- Query embedding uses input_type="query" (Voyage asymmetric retrieval).
- Empty/whitespace query → empty result.
- Threshold: filters out very weak matches (similarity below `min_similarity`).

Notes:
- Model change (Voyage model) requires re-embedding stored chunks.
  Mismatched models produce meaningless similarity.
- Current embedding dimension is 1024 (from app.embeddings.base).
"""

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import (
    EmbeddingError,
    EmbeddingProvider,
    get_embedding_provider,
)
from app.retrieval.types import SemanticHit


class SemanticRetriever:
    """Voyage-embedding semantic retriever over policy_chunks."""

    def __init__(
        self,
        session: AsyncSession,
        provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.session = session
        self.provider = provider or get_embedding_provider()

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SemanticHit]:
        """
        Retrieve top-K chunks ranked by cosine similarity.

        Args:
            query: Natural-language query string.
            limit: Max number of hits.
            min_similarity: Filter threshold (0.0-1.0).
                Set to 0.0 for no filtering.
        """
        if not query or not query.strip():
            return []

        # 1. Embed the query
        try:
            vectors, _ = await self.provider.embed_batch(
                [query.strip()],
                input_type="query",
            )
        except EmbeddingError:
            return []

        query_vector = vectors[0]

        # 2. pgvector cosine search
        #    `<=>` returns cosine DISTANCE (0 = identical, 2 = opposite)
        #    Similarity = 1 - distance
        stmt = text(
            """
            SELECT
                id,
                source_record_id,
                chunk_index,
                chunk_text,
                1 - (embedding <=> CAST(:vec AS vector)) AS similarity
            FROM policy_chunks
            WHERE 1 - (embedding <=> CAST(:vec AS vector)) >= :min_sim
            ORDER BY embedding <=> CAST(:vec AS vector)
            LIMIT :lim
            """
        )

        result = await self.session.execute(
            stmt,
            {
                "vec": _vector_literal(query_vector),
                "min_sim": min_similarity,
                "lim": limit,
            },
        )
        rows = result.fetchall()

        hits: list[SemanticHit] = []
        for row in rows:
            hits.append(
                SemanticHit(
                    chunk_id=row.id,
                    source_record_id=row.source_record_id,
                    chunk_index=row.chunk_index,
                    chunk_text=row.chunk_text,
                    similarity=float(row.similarity),
                )
            )
        return hits


def _vector_literal(values: list[float]) -> str:
    """
    Convert a Python list of floats into pgvector's text literal.

    Format: '[0.1,0.2,0.3]'
    """
    inner = ",".join(f"{v:.8f}" for v in values)
    return f"[{inner}]"