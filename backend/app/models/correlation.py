"""
Correlation models.

A Correlation represents a relationship between two source records
that belong to the same operational situation.

Example:
- source_record_a = Supplier S-1042 (from Supplier DB)
- source_record_b = PO-4821 (from Procurement DB)
- relationship_type = "supplier_has_purchase_order"
- basis = "exact_id"  (S-1042 was found in the PO record)
- confidence = 1.0

Correlation is a REAL backend capability (not decorative graph).
Deterministic matching is preferred; semantic matching is a
fallback that produces lower confidence scores.

Design notes:
- Self-reference (record_a == record_b) is prevented at DB level.
- Inverse relationships (A -> B vs B -> A) are NOT prevented at DB level;
  the Correlation Engine is responsible for emitting one canonical direction.
- Confidence is a trust/strength score, not a calibrated probability.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Correlation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A relationship between two source records.

    Lifecycle:
    1. Created by Correlation Engine (Stage 8)
    2. Used by Context Construction to build connected view
    3. Optionally verified by human review

    Basis values:
    - "exact_id"      -> direct foreign key match (confidence = 1.0)
    - "business_key"  -> shared business key like PO number
    - "semantic"      -> embedding similarity (confidence < 1.0)
    """

    __tablename__ = "correlations"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this correlation is part of",
    )

    record_a_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="First record in the relationship",
    )

    record_b_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Second record in the relationship",
    )

    relationship_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g., supplier_has_purchase_order",
    )

    basis: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="exact_id | business_key | semantic",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        server_default="1.0",
        comment=(
            "Trust/strength score for this correlation. "
            "1.0 = deterministic (fully trusted). "
            "Lower values = less certain (semantic). "
            "Range: 0.0 - 1.0"
        ),
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment=(
            "Whether a human has verified this correlation. "
            "Actor/timestamp captured in audit log, not here."
        ),
    )

    correlation_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Matching values, evidence, etc.",
    )

    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "record_a_id",
            "record_b_id",
            "relationship_type",
            name="uq_correlations_task_pair_type",
        ),
        CheckConstraint(
            "record_a_id <> record_b_id",
            name="ck_correlations_no_self_reference",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_correlations_confidence_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Correlation id={self.id} "
            f"type={self.relationship_type!r} "
            f"basis={self.basis!r} "
            f"confidence={self.confidence}>"
        )