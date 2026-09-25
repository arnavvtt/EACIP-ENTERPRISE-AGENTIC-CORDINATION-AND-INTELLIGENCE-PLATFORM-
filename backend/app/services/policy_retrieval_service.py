"""
Policy Retrieval Service (Stage 10.6).

Orchestrates hybrid retrieval over policy_chunks:
    1. Lexical retrieval (PostgreSQL FTS)
    2. Semantic retrieval (Voyage embeddings + pgvector)
    3. RRF fusion

Returns a unified ranked list of policy chunks.

Design:
- Read-only (does not persist retrieved_records here; that comes in
  Stage 10.7 when we integrate with the task pipeline).
- Idempotent from the caller's perspective.
- Uses retrievers directly; the service is thin orchestration.
"""

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval import (
    LexicalRetriever,
    SemanticRetriever,
    reciprocal_rank_fusion,
)
from app.retrieval.types import FusedHit


@dataclass
class HybridRetrievalResult:
    """Result of a hybrid retrieval call."""

    query: str
    fused_hits: list[FusedHit] = field(default_factory=list)
    lexical_count: int = 0
    semantic_count: int = 0


class PolicyRetrievalService:
    """Hybrid (lexical + semantic + RRF) policy retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lexical = LexicalRetriever(session)
        self.semantic = SemanticRetriever(session)

    async def search(
        self,
        query: str,
        limit: int = 10,
        per_retriever_limit: int = 10,
    ) -> HybridRetrievalResult:
        """
        Run hybrid retrieval for a query.

        Args:
            query: Natural-language query.
            limit: Final fused top-K returned.
            per_retriever_limit: How many hits from each retriever
                                 before fusion.

        Returns:
            HybridRetrievalResult with fused hits + counts.
        """
        if not query or not query.strip():
            return HybridRetrievalResult(query=query or "")

        lexical_hits = await self.lexical.retrieve(
            query, limit=per_retriever_limit
        )
        semantic_hits = await self.semantic.retrieve(
            query, limit=per_retriever_limit
        )

        fused = reciprocal_rank_fusion(lexical_hits, semantic_hits)

        return HybridRetrievalResult(
            query=query.strip(),
            fused_hits=fused[:limit],
            lexical_count=len(lexical_hits),
            semantic_count=len(semantic_hits),
        )