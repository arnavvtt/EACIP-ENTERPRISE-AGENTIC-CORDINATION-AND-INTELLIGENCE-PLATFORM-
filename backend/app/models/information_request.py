"""
Information Request models.

An InformationRequest represents a request for missing information.

It can originate from:
1. Phase 1: A human review decision of "info_requested"
   (no workflow exists yet — workflow_id is NULL)
2. Phase 2: Workflow execution discovering missing info
   (workflow_id is set)

This is why workflow_id is nullable while task_id is mandatory.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class InformationRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A request for missing information.

    Lifecycle:
    1. Created (from a validation, human review, or manually)
    2. Target role is notified
    3. Target role responds
    4. Response is validated and/or used to update context
    5. Request is resolved
    """

    __tablename__ = "information_requests"

    workflow_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment=(
            "Workflow this request belongs to. NULL if the request "
            "originated in Phase 1 (before any workflow exists)."
        ),
    )

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this request is for",
    )

    validation_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("validations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Validation that triggered this request (if any)",
    )

    request_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="missing_document | clarification | verification | other",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What information is being requested",
    )

    target_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Role expected to respond",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
        server_default="open",
        index=True,
        comment="open | responded | resolved | cancelled",
    )

    response_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Response payload (structure varies by request type)",
    )

    response_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text notes from the responder",
    )

    request_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra info: deadline, priority, etc.",
    )

    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<InformationRequest id={self.id} "
            f"type={self.request_type!r} "
            f"status={self.status!r}>"
        )