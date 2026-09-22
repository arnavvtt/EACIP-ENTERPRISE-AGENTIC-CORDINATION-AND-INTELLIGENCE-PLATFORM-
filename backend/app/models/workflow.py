"""
Workflow models.

A Workflow represents the Phase 2 coordination lifecycle for an
approved operational package. It decomposes work into steps,
each with dependencies, and tracks progress until completion.

Design notes:
- A task may have multiple workflows over time (re-runs).
- Steps use `depends_on` as a JSONB list of step IDs for flexibility.
- Actor identity (who did what) is in the audit log, not here yet.

IMPORTANT invariant:
    The referenced package MUST have status='approved'.
    This is enforced by the service layer when creating a workflow.
    The database does not enforce it (would require triggers or
    composite FKs, which are overkill for the prototype).
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Workflow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A Phase 2 coordination workflow for an approved package.

    Lifecycle:
    1. Created when a package is approved (Stage 13)
    2. Steps defined from a template
    3. Steps executed, responses collected
    4. Workflow status moves: pending -> active -> completed
    """

    __tablename__ = "workflows"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task this workflow is for",
    )

    package_id: Mapped[UUID] = mapped_column(
        ForeignKey("operational_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment=(
            "Approved package that initiated this workflow. "
            "IMPORTANT: The referenced package MUST have status='approved'. "
            "This invariant is enforced by the service layer "
            "(see Stage 13), not by a DB constraint."
        ),
    )

    template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Workflow template used (e.g., supplier_onboarding_v1)",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="pending | active | completed | cancelled | failed",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of this workflow instance",
    )

    workflow_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra metadata (initiator context, etc.)",
    )

    task: Mapped["Task"] = relationship()  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<Workflow id={self.id} "
            f"template={self.template_name!r} "
            f"status={self.status!r}>"
        )


class WorkflowStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    One step within a workflow.

    Steps are the atomic units of coordination. Each step has:
    - an optional responsible role
    - dependency on other steps
    - a status
    - optional approval gate

    Status values:
    - "pending"     -> not yet started
    - "in_progress" -> currently being worked on
    - "blocked"     -> waiting on dependency or response
    - "completed"   -> done
    - "skipped"     -> not applicable
    - "failed"      -> errored out
    """

    __tablename__ = "workflow_steps"

    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Workflow this step belongs to",
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Order within the workflow (for display)",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Step name (e.g., 'Verify compliance certifications')",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the step",
    )

    responsible_role: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Role responsible for this step (e.g., 'compliance_officer')",
    )

    depends_on: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        comment=(
            "List of step IDs this step depends on. Stored as JSONB "
            "because steps are immutable after workflow creation and "
            "reverse dependency queries are not required in the current "
            "prototype. If reverse queries become necessary, refactor "
            "to a separate dependency table."
        ),
    )

    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether this step requires explicit approval",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="pending | in_progress | blocked | completed | skipped | failed",
    )

    step_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra info: inputs required, outputs expected, etc.",
    )

    workflow: Mapped["Workflow"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<WorkflowStep id={self.id} "
            f"name={self.name!r} "
            f"status={self.status!r}>"
        )