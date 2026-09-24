"""
Requirement repository — data access for the task_requirements table.

No commit — caller (service) owns the transaction.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_requirement import TaskRequirement


class RequirementRepository:
    """Repository for the `task_requirements` table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_by_task_id(self, task_id: UUID) -> int:
        """Delete all requirements for a task. Returns count deleted."""
        result = await self.session.execute(
            delete(TaskRequirement).where(TaskRequirement.task_id == task_id)
        )
        return result.rowcount or 0

    async def create_many(
        self,
        task_id: UUID,
        rows: list[dict[str, Any]],
    ) -> list[TaskRequirement]:
        """
        Bulk insert requirements for a task.

        Each row dict must contain:
            requirement_type, description, is_mandatory,
            source_hint, priority, requirement_metadata
        """
        created: list[TaskRequirement] = []
        for row in rows:
            req = TaskRequirement(
                task_id=task_id,
                requirement_type=row["requirement_type"],
                description=row["description"],
                is_mandatory=row["is_mandatory"],
                source_hint=row.get("source_hint"),
                priority=row["priority"],
                requirement_metadata=row.get("requirement_metadata", {}),
            )
            self.session.add(req)
            created.append(req)

        await self.session.flush()
        return created

    async def get_by_task_id(self, task_id: UUID) -> list[TaskRequirement]:
        """Return all requirements for a task, ordered by priority."""
        result = await self.session.execute(
            select(TaskRequirement)
            .where(TaskRequirement.task_id == task_id)
            .order_by(TaskRequirement.priority)
        )
        return list(result.scalars().all())