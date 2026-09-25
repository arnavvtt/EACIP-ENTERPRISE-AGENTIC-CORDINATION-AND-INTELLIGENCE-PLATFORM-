"""
PolicyChunk model.

Stores chunked policy documents with their BGE-M3 embeddings
(1024-dim) for semantic retrieval.

Chunking and embedding ingestion happens in Stage 10.3.
Semantic retrieval + vector index design happens in Stage 10.5.

Notes:
- EMBEDDING_DIMENSIONS comes from app.embeddings.base (single source of truth).
  Do NOT duplicate a literal dimension here.
- No vector index yet. It will be added in Stage 10.5 after actual data
  is available and the retrieval workload is understood.
"""

from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.embeddings.base import EMBEDDING_DIMENSIONS
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class PolicyChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A chunk of a policy document with its embedding.

    Lifecycle:
    1. Created by ingestion service (Stage 10.3)
    2. Searched via cosine similarity (Stage 10.5)
    3. Referenced by retrieved_records (same table as Stage 6)
    """

    __tablename__ = "policy_chunks"

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent policy document (source_record)",
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Zero-based order of this chunk within the document",
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Actual chunk content (used for lexical + context display)",
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=False,
        comment="Dense embedding (dimension from app.embeddings.base)",
    )

    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Provider, model, version, timestamps for re-embedding",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_record_id",
            "chunk_index",
            name="uq_policy_chunks_source_chunk",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<PolicyChunk id={self.id} "
            f"source={self.source_record_id} idx={self.chunk_index}>"
        )
    