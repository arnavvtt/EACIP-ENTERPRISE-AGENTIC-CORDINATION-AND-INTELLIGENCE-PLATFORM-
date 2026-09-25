"""
Policy API routes.

Endpoints:
- POST /policies/search    Hybrid (lexical + semantic + RRF) search
- GET  /policies/chunks    List all chunks (debugging/inspection)
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import PolicyChunkRepository
from app.schemas.policy_retrieval import (
    FusedChunkResponse,
    HybridRetrievalResponse,
)
from app.services import PolicyRetrievalService

router = APIRouter(prefix="/policies", tags=["policies"])


def get_policy_retrieval_service(
    db: AsyncSession = Depends(get_db),
) -> PolicyRetrievalService:
    return PolicyRetrievalService(db)


def get_policy_chunk_repo(
    db: AsyncSession = Depends(get_db),
) -> PolicyChunkRepository:
    return PolicyChunkRepository(db)


@router.post(
    "/search",
    response_model=HybridRetrievalResponse,
    summary="Hybrid policy search (lexical + semantic + RRF)",
)
async def search_policies(
    query: str = Query(..., min_length=1, max_length=1000),
    limit: int = Query(10, ge=1, le=50),
    service: PolicyRetrievalService = Depends(get_policy_retrieval_service),
) -> HybridRetrievalResponse:
    """
    Run hybrid retrieval for a query.

    Returns the top-K fused chunks ranked by RRF score.
    """
    result = await service.search(query=query, limit=limit)
    return HybridRetrievalResponse(
        query=result.query,
        lexical_count=result.lexical_count,
        semantic_count=result.semantic_count,
        total_fused=len(result.fused_hits),
        hits=[
            FusedChunkResponse(
                chunk_id=h.chunk_id,
                source_record_id=h.source_record_id,
                chunk_index=h.chunk_index,
                chunk_text=h.chunk_text,
                rrf_score=h.rrf_score,
                lexical_rank=h.lexical_rank,
                semantic_rank=h.semantic_rank,
            )
            for h in result.fused_hits
        ],
    )


@router.get(
    "/chunks",
    summary="List all policy chunks (debugging)",
)
async def list_policy_chunks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: PolicyChunkRepository = Depends(get_policy_chunk_repo),
) -> dict:
    chunks = await repo.list_all(limit=limit, offset=offset)
    total = await repo.count()
    return {
        "total": total,
        "returned": len(chunks),
        "chunks": [
            {
                "id": str(c.id),
                "source_record_id": str(c.source_record_id),
                "chunk_index": c.chunk_index,
                "chunk_text": c.chunk_text[:200],
                "chunk_metadata": c.chunk_metadata,
            }
            for c in chunks
        ],
    }