"""
Audit Log models.

An AuditLog is an append-only event record. Every important action
in EACIP produces one or more entries here.

Design principles:
- Append-only: rows are never updated or deleted (application-level
  convention — see class docstring).
- Generic: one table for all event types across the system.
- Polymorphic: entity_type + entity_id can reference any record.
- Flexible payload: details JSONB stores event-specific info.

Reference strategy:
- entity_type + entity_id: polymorphic, no FK, survives any deletion.
- task_id: real FK with ON DELETE SET NULL (convenience + index).

Examples of event_type:
- "task.created"
- "task.status_changed"
- "retrieval.executed"
- "validation.detected"
- "package.generated"
- "package.approved"
- "workflow.started"
- "workflow.step.completed"
- "information_request.sent"
- "information_request.responded"

Actor field is reserved for future authentication. Until then,
it can be NULL or a system identifier.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    An append-only audit event.

    IMPORTANT: "Append-only" is an APPLICATION-LEVEL convention,
    not a database-enforced invariant. The model itself does not
    prevent UPDATE or DELETE. Application code (services) must
    never modify or delete audit log rows.

    If stronger enforcement is required in production, options are:
    - DB permissions (REVOKE UPDATE/DELETE)
    - DB triggers (reject UPDATE/DELETE)
    These are deliberately NOT used in the prototype to avoid
    unnecessary complexity.

    Note: This model does NOT use TimestampMixin because that mixin
    adds an `updated_at` column, which contradicts the append-only
    design of an audit log.
    """

    __tablename__ = "audit_logs"

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Event identifier, e.g., 'task.created', 'package.approved'",
    )

    entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of the entity involved, e.g., 'task', 'package'",
    )

    entity_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        comment="ID of the specific entity involved (no FK; entity may be deleted)",
    )

    task_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment=(
            "Convenience FK to tasks (for task-level queries and indexing). "
            "Unlike entity_type/entity_id (which are polymorphic and have no FK), "
            "this is a real FK. ON DELETE SET NULL ensures the audit log "
            "survives task deletion while preserving the linkage until then."
        ),
    )

    actor: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Actor identifier. NULL until auth is implemented.",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
        server_default="info",
        comment="info | warning | error",
    )

    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Event-specific payload",
    )

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When this event occurred (immutable)",
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} "
            f"event={self.event_type!r} "
            f"entity={self.entity_type!r}>"
        )