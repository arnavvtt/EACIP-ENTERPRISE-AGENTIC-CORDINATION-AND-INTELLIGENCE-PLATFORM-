"""
Retrieved record models.

A RetrievedRecord links a task (and optionally a requirement) to a
source record that was fetched during retrieval.

This is the BRIDGE between:
- Task (what we're working on)
- Requirement (what we needed)
- SourceRecord (what we found)

Why this is a separate table (not just adding task_id to source_records):
- A source record can be retrieved for multiple tasks
- We track retrieval method and relevance per retrieval
- Research evaluation needs precision/recall per task
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class RetrievedRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A record retrieved for a specific task.

    Lifecycle:
    1. Created by Retrieval Engine (Stage 6)
    2. Used by Correlation (Stage 8) to find relationships
    3. Used by Validation (Stage 9) to check completeness
    4. Filtered by "is_selected" before being placed in the package

    Retrieval method:
    - "sql_query" — direct DB query
    - "vector_search" — semantic search
    - "api_call" — external API
    - "rule_based" — deterministic rule
    """

    __tablename__ = "retrieved_records"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this retrieval was for",
    )

    requirement_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("task_requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Requirement this retrieval satisfies (if applicable)",
    )

    source_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The actual source record that was retrieved",
    )

    retrieval_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="sql_query | vector_search | api_call | rule_based",
    )

    relevance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Relevance score 0.0-1.0 (if applicable)",
    )

    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether this record is selected for the final context",
    )

    retrieval_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Query used, time taken, etc.",
    )

    # Relationships
    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    # Unique: same source record shouldn't be retrieved twice for same task
    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "source_record_id",
            name="uq_retrieved_records_task_source",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RetrievedRecord id={self.id} "
            f"method={self.retrieval_method!r} "
            f"selected={self.is_selected}>"
        )