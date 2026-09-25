"""
Validation repository — data access for `validations` table.
No commit — caller (service) owns the transaction.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import Validation


class ValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_by_task_id(self, task_id: UUID) -> int:
        result = await self.session.execute(
            delete(Validation).where(Validation.task_id == task_id)
        )
        return result.rowcount or 0

    async def create_many(
        self,
        task_id: UUID,
        rows: list[dict[str, Any]],
    ) -> list[Validation]:
        created: list[Validation] = []
        for row in rows:
            v = Validation(
                task_id=task_id,
                requirement_id=row.get("requirement_id"),
                validation_type=row["validation_type"],
                severity=row["severity"],
                description=row["description"],
                details=row.get("details", {}),
                status=row.get("status", "open"),
            )
            self.session.add(v)
            created.append(v)
        await self.session.flush()
        return created

    async def get_by_task_id(self, task_id: UUID) -> list[Validation]:
        result = await self.session.execute(
            select(Validation)
            .where(Validation.task_id == task_id)
            .order_by(Validation.created_at)
        )
        return list(result.scalars().all())