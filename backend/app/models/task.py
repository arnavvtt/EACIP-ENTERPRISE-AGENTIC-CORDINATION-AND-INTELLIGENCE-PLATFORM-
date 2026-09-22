"""
Task model — the central entity of EACIP.

Every operational task submitted by a user is stored here.
All other entities (requirements, retrieved records, packages,
workflows) reference back to a task.
"""

from typing import Any, Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an operational task submitted by a user.

    Lifecycle:
    1. Created on user submission (status = 'pending')
    2. Processing begins (status = 'processing')
    3. Task understanding extracts intent + entities (Stage 4)
    4. Requirements identified (Stage 5)
    5. ... rest of pipeline ...
    6. Final status = 'completed' or 'rejected'

    The `use_case` column is optional because tasks can be submitted
    before knowing which use case they belong to. The use case may be
    inferred during understanding.
    """

    __tablename__ = "tasks"

    # ------------------------------------------------------------------
    # Core fields
    # ------------------------------------------------------------------
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Short human-readable title of the task",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Raw task description as submitted by the user",
    )

    use_case: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Use case identifier (e.g., supplier_qualification, purchase_delay)",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Current status: pending, processing, ready, under_review, approved, rejected, completed",
    )

    # ------------------------------------------------------------------
    # Understanding fields (filled in Stage 4)
    # ------------------------------------------------------------------
    intent: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Extracted task intent (e.g., investigate, resolve, verify)",
    )

    # ------------------------------------------------------------------
    # Flexible metadata (JSONB)
    # ------------------------------------------------------------------
    task_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Flexible metadata: priority, source hints, custom fields",
    )

    # ------------------------------------------------------------------
    # Representation (for debugging)
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status!r}>"