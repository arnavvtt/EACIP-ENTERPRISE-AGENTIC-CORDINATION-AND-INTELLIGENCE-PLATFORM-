"""
Task repository — data access layer for the tasks table.

All SQL/ORM operations for tasks live here. Services call these
methods instead of writing queries directly.

IMPORTANT:
- Repository does NOT commit transactions.
- Repository does NOT import API schemas.
- Service layer owns the transaction boundary.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


class TaskRepository:
    """Repository for the `tasks` table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        title: str,
        description: str,
        use_case: Optional[str] = None,
    ) -> Task:
        """
        Insert a new task and return it.

        NOTE: Does NOT commit. Caller (service) must commit.

        Uses flush() to send INSERT to DB and get the ID back,
        but leaves the transaction open so multiple operations
        can be grouped by the service.
        """
        task = Task(
            title=title,
            description=description,
            use_case=use_case,
            status="pending",
            task_metadata={},
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: UUID) -> Optional[Task]:
        """Fetch a single task by its UUID, or None if not found."""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[Task]:
        """Fetch a list of tasks, newest first."""
        result = await self.session.execute(
            select(Task)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return total number of tasks."""
        result = await self.session.execute(
            select(func.count()).select_from(Task)
        )
        return result.scalar_one()