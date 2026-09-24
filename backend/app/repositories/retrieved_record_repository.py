"""
Retrieved Record repository — data access for `retrieved_records` table.

No commit — caller (service) owns the transaction.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.retrieved_record import RetrievedRecord


class RetrievedRecordRepository:
    """Repository for the `retrieved_records` table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_by_task_id(self, task_id: UUID) -> int:
        result = await self.session.execute(
            delete(RetrievedRecord).where(RetrievedRecord.task_id == task_id)
        )
        return result.rowcount or 0

    async def create_many(
        self,
        task_id: UUID,
        rows: list[dict[str, Any]],
    ) -> list[RetrievedRecord]:
        """
        Bulk insert retrieved records.

        Each row must contain:
            requirement_id, source_record_id, retrieval_method,
            relevance_score, is_selected, retrieval_metadata
        """
        created: list[RetrievedRecord] = []
        for row in rows:
            rec = RetrievedRecord(
                task_id=task_id,
                requirement_id=row.get("requirement_id"),
                source_record_id=row["source_record_id"],
                retrieval_method=row["retrieval_method"],
                relevance_score=row.get("relevance_score"),
                is_selected=row.get("is_selected", True),
                retrieval_metadata=row.get("retrieval_metadata", {}),
            )
            self.session.add(rec)
            created.append(rec)
        await self.session.flush()
        return created

    async def get_by_task_id(self, task_id: UUID) -> list[RetrievedRecord]:
        result = await self.session.execute(
            select(RetrievedRecord)
            .where(RetrievedRecord.task_id == task_id)
            .order_by(RetrievedRecord.created_at)
        )
        return list(result.scalars().all())