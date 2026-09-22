"""
Operational Package models.

The Operational Package is the primary output of Phase 1
(Operational Context Preparation). It is a structured, human-
reviewable artifact containing:

1. Task Summary
2. Relevant Entities
3. Required Context
4. Retrieved Information
5. Correlated Information
6. Historical Context
7. Information Gaps
8. Potential Inconsistencies
9. Relevant Policies / Knowledge
10. Source Traceability
11. AI-Assisted Insights + Possible Next Steps

Design notes:
- Sections stored as JSONB for flexibility (structure may evolve).
- Version column allows multiple iterations (edit -> new version).
- Actual generation happens in Stage 11; this table stores the result.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class OperationalPackage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A structured operational package for a task.

    Lifecycle:
    1. Draft created by Package Generator (Stage 11)
    2. Status moves to 'ready_for_review'
    3. Human reviews (see HumanReview)
    4. Status becomes 'approved' or 'rejected'
    5. If edits requested, a new version is created;
       the previous version's status becomes 'superseded'

    Status values:
    - "draft"              -> being generated
    - "ready_for_review"   -> completed, awaiting human
    - "approved"           -> human approved
    - "rejected"           -> human rejected
    - "superseded"         -> a newer version exists
    """

    __tablename__ = "operational_packages"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this package belongs to",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Version number (increments on re-generation)",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
        comment="draft | ready_for_review | approved | rejected | superseded",
    )

    sections: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="The 11 structured sections of the package",
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Short LLM-generated summary of the package",
    )

    generated_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="system",
        server_default="system",
        comment="Generator identifier (e.g., 'system', 'system+v1.2.0')",
    )

    package_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Prompt version, tokens used, generation time, etc.",
    )

    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "version",
            name="uq_operational_packages_task_version",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OperationalPackage id={self.id} "
            f"version={self.version} "
            f"status={self.status!r}>"
        )