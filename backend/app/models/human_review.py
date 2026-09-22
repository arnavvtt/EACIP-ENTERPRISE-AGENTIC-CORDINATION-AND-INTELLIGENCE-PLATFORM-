"""
Human Review models.

A HumanReview captures a decision made by a human reviewer on an
Operational Package. This is EACIP's human-in-the-loop control point.

Design notes:
- Multiple reviews per package are allowed (reject -> edit -> review).
- Actor identity is NOT stored here; it will be captured in the
  audit log when authentication is implemented.
- `edited_sections` stores only the diff; the authoritative
  package remains in operational_packages.
- `task_id` is intentionally kept alongside `package_id` for
  task-level query performance and audit clarity. This is an
  accepted denormalization trade-off (small redundancy vs query cost).
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class HumanReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A human decision on an operational package.

    Decision values and their lifecycle semantics:

    - "approved"
        Package accepted as-is. This package becomes authoritative
        and Phase 2 (Governed Coordination) may begin.

    - "rejected"
        Package rejected. No further action unless a new package
        is generated.

    - "edited"
        Human edited one or more sections AND intends to approve
        the edited version. Lifecycle:
          1. A new package version is created with the edits.
          2. The previous package version is marked "superseded".
          3. This review references the NEW package (the authoritative one).
          4. `edited_sections` stores the diff for audit purposes.
          5. The new package must subsequently be approved before
             Phase 2 begins.
        `edited_sections` is REQUIRED when decision='edited'
        (enforced by CHECK constraint).

    - "info_requested"
        Additional information is needed before a final decision.
        No package status change yet.

    Phase 2 gate:
        A HumanReview with decision in ("approved", "edited")
        referencing an approved package is what allows Phase 2 to start.
    """

    __tablename__ = "human_reviews"

    # Kept for task-level query clarity (accepted denormalization).
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this review is for (denormalized for query clarity)",
    )

    package_id: Mapped[UUID] = mapped_column(
        ForeignKey("operational_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Package being reviewed (authoritative package)",
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="approved | rejected | edited | info_requested",
    )

    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional human reasoning / notes",
    )

    edited_sections: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Diff of edited sections (required when decision='edited')",
    )

    review_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Time taken, UI context, etc.",
    )

    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (
        CheckConstraint(
            "decision <> 'edited' OR edited_sections IS NOT NULL",
            name="ck_human_reviews_edited_requires_diff",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<HumanReview id={self.id} "
            f"decision={self.decision!r}>"
        )