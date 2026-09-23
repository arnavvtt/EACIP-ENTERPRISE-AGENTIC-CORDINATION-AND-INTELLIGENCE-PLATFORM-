"""
Task service — business logic for tasks.

The service layer:
- Orchestrates multiple repository calls.
- Owns the transaction boundary (commit/rollback).
- Contains business rules that aren't just data access.

Repository is injected via constructor (dependency injection).
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories import TaskRepository
from app.schemas.task import TaskCreate


class TaskService:
    """
    Business logic for tasks.

    Usage:
        service = TaskService(session)
        task = await service.create_task(TaskCreate(...))
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TaskRepository(session)

    async def create_task(self, data: TaskCreate) -> Task:
        """
        Create a new task.

        This is the transaction boundary. If anything inside fails,
        the whole operation rolls back — no partial data.
        """
        try:
            task = await self.repo.create(
                title=data.title,
                description=data.description,
                use_case=data.use_case,
            )
            # Future: create requirements, audit log, etc. here
            # (all in same transaction)

            await self.session.commit()
            await self.session.refresh(task)
            return task
        except Exception:
            await self.session.rollback()
            raise

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Fetch a single task by ID."""
        return await self.repo.get_by_id(task_id)

    async def list_tasks(
        self, limit: int = 100, offset: int = 0
    ) -> tuple[list[Task], int]:
        """
        Fetch a paginated list of tasks and total count.

        Returns: (tasks, total_count)
        """
        tasks = await self.repo.list_all(limit=limit, offset=offset)
        total = await self.repo.count()
        return tasks, total