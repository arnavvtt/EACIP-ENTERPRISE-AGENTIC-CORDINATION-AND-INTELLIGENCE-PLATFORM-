"""
Validation models.

A Validation represents a finding produced by the Context
Validation stage (Stage 9).

Two main types:
1. missing_requirement  -> required info was not found
2. inconsistency        -> conflicting values across sources

EACIP does NOT auto-resolve inconsistencies. It flags them
for human verification. This is by design (validation before
reliance, human authority).

Design note on provenance:
- Missing-requirement validations do not involve source records.
- Inconsistency validations involve 2+ source records (could be N-way).
- Instead of fixed columns (record_a_id, record_b_id), the
  `details` JSONB stores a structured list:
    {
      "field": "payment_terms",
      "values": [
        {"record_id": "<uuid>", "value": "Net 45", "source": "Supplier DB"},
        {"record_id": "<uuid>", "value": "Net 30", "source": "Procurement DB"}
      ]
    }
  This keeps the schema flexible for 2-way, 3-way, or missing cases
  while preserving provenance.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Validation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A validation finding for a task.

    Lifecycle:
    1. Created by Validation Engine (Stage 9)
    2. Shown in Context Workspace
    3. Human can acknowledge or resolve
    4. Included in Operational Package

    Severity:
    - "low"    -> minor observation
    - "medium" -> needs attention but not blocking
    - "high"   -> blocking; package cannot be approved

    Status:
    - "open"         -> just detected
    - "acknowledged" -> human has seen it
    - "resolved"     -> human resolved it (may include manual fix)
    """

    __tablename__ = "validations"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this validation belongs to",
    )

    requirement_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("task_requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Requirement this validation relates to (if applicable)",
    )

    validation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="missing_requirement | inconsistency | incomplete_context",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        server_default="medium",
        comment="low | medium | high",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable summary of the finding",
    )

    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment=(
            "Structured details. For inconsistency, should contain "
            "'values': [{'record_id': UUID, 'value': ..., 'source': ...}, ...] "
            "to preserve provenance of conflicting values."
        ),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        server_default="open",
        comment="open | acknowledged | resolved",
    )

    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<Validation id={self.id} "
            f"type={self.validation_type!r} "
            f"severity={self.severity!r} "
            f"status={self.status!r}>"
        )