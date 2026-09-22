"""
Assignment models.

An Assignment links a workflow step to a responsible party.
Since users/auth are not implemented yet, assignments use roles
rather than user IDs.

When authentication is added later, assignments may reference
actual users in addition to (or instead of) roles.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Assignment of a workflow step to a role.

    Lifecycle:
    1. Created when a workflow is instantiated (Stage 13)
    2. Role is notified / becomes responsible
    3. Role completes the step, or requests help
    4. Assignment is closed
    """

    __tablename__ = "assignments"

    workflow_step_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Step being assigned",
    )

    assigned_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Role responsible (e.g., procurement_manager)",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="assigned",
        server_default="assigned",
        index=True,
        comment="assigned | accepted | completed | declined | reassigned",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes from or for the assignee",
    )

    assignment_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra info: SLA, urgency, etc.",
    )

    workflow_step: Mapped["WorkflowStep"] = relationship()  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<Assignment id={self.id} "
            f"role={self.assigned_role!r} "
            f"status={self.status!r}>"
        )