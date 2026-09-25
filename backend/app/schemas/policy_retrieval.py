"""
Schemas for policy hybrid retrieval API.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FusedChunkResponse(BaseModel):
    """A single fused retrieval hit."""

    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID
    source_record_id: UUID
    chunk_index: int
    chunk_text: str
    rrf_score: float
    lexical_rank: int | None = None
    semantic_rank: int | None = None


class HybridRetrievalResponse(BaseModel):
    """Response for POST /policies/search."""

    query: str
    lexical_count: int
    semantic_count: int
    total_fused: int
    hits: list[FusedChunkResponse] = Field(default_factory=list)