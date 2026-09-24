"""
Correlation repository — data access for `correlations` table.
No commit — caller (service) owns the transaction.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.correlation import Correlation


class CorrelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_by_task_id(self, task_id: UUID) -> int:
        result = await self.session.execute(
            delete(Correlation).where(Correlation.task_id == task_id)
        )
        return result.rowcount or 0

    async def create_many(
        self,
        task_id: UUID,
        rows: list[dict[str, Any]],
    ) -> list[Correlation]:
        created: list[Correlation] = []
        for row in rows:
            corr = Correlation(
                task_id=task_id,
                record_a_id=row["record_a_id"],
                record_b_id=row["record_b_id"],
                relationship_type=row["relationship_type"],
                basis=row["basis"],
                confidence=row["confidence"],
                is_verified=False,
                correlation_metadata=row.get("correlation_metadata", {}),
            )
            self.session.add(corr)
            created.append(corr)
        await self.session.flush()
        return created

    async def get_by_task_id(self, task_id: UUID) -> list[Correlation]:
        result = await self.session.execute(
            select(Correlation)
            .where(Correlation.task_id == task_id)
            .order_by(Correlation.created_at)
        )
        return list(result.scalars().all())