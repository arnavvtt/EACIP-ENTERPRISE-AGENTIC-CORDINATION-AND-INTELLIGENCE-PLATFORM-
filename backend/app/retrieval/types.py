"""
Retrieval types.

Provider-agnostic shapes for retrieval results. Used across
retrievers and the retrieval service.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID


@dataclass
class RetrievedRecordData:
    """
    A single retrieved record candidate (Stage 6 — structured/entity).

    NOTE: This is NOT the DB row. The service converts these into
    `retrieved_records` rows after aggregation/deduplication.
    """

    source_record_id: UUID
    source_key: str
    record_type: str
    external_id: str
    retrieval_method: str
    relevance_score: Optional[float] = None
    match_reason: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LexicalHit:
    """A single result from lexical (PostgreSQL FTS) retrieval."""

    chunk_id: UUID
    source_record_id: UUID
    chunk_index: int
    chunk_text: str
    rank: float
    """PostgreSQL ts_rank_cd score (higher = more relevant)."""


@dataclass
class SemanticHit:
    """A single result from semantic (vector) retrieval."""

    chunk_id: UUID
    source_record_id: UUID
    chunk_index: int
    chunk_text: str
    similarity: float
    """Cosine similarity 0.0-1.0 (higher = more similar)."""


@dataclass
class FusedHit:
    """A single result after RRF fusion of lexical + semantic."""

    chunk_id: UUID
    source_record_id: UUID
    chunk_index: int
    chunk_text: str
    rrf_score: float
    lexical_rank: Optional[int] = None
    semantic_rank: Optional[int] = None