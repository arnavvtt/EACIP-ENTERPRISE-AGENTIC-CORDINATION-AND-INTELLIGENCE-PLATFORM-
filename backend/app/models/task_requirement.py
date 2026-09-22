"""
Task requirement models.

A TaskRequirement represents one piece of information needed for a task.
Example: For "Supplier Qualification", requirements might be:
- financial_info (mandatory)
- compliance_certifications (mandatory)
- quality_history (mandatory)
- esg_evidence (mandatory)
- delivery_performance (optional)

These are identified in Stage 5 (Requirement Engine) and are used to
guide retrieval in Stage 6.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TaskRequirement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    One piece of information required for a task.

    Lifecycle:
    1. Created by Requirement Engine (Stage 5)
    2. Used by Retrieval (Stage 6) to know what to fetch
    3. Referenced by Validation (Stage 9) to check coverage

    Why separate table (not JSONB in tasks):
    - Query coverage per requirement type
    - Track each requirement's retrieval status
    - Research evaluation (which requirements were covered?)
    """

    __tablename__ = "task_requirements"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this requirement belongs to",
    )

    requirement_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type: financial_info, compliance_cert, quality_history, etc.",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable description of what's needed",
    )

    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether this requirement must be satisfied",
    )

    source_hint: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Optional hint on which source to use",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Priority order (1 = highest)",
    )

    requirement_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra metadata about the requirement",
    )

    # Relationship back to task
    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<TaskRequirement id={self.id} "
            f"type={self.requirement_type!r} "
            f"mandatory={self.is_mandatory}>"
        )