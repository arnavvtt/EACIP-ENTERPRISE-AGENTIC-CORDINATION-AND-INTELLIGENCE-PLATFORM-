"""
Operational Package repository.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operational_package import OperationalPackage


class PackageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, task_id: UUID, sections: dict[str, Any], summary: str = ""
    ) -> OperationalPackage:
        # Find current max version for this task
        stmt = (
            select(OperationalPackage.version)
            .where(OperationalPackage.task_id == task_id)
            .order_by(OperationalPackage.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        current_version = result.scalar_one_or_none()
        next_version = (current_version or 0) + 1

        pkg = OperationalPackage(
            task_id=task_id,
            version=next_version,
            status="ready_for_review",
            sections=sections,
            summary=summary,
            generated_by="system",
            package_metadata={},
        )
        self.session.add(pkg)
        await self.session.flush()
        return pkg

    async def get_latest_for_task(self, task_id: UUID) -> OperationalPackage | None:
        stmt = (
            select(OperationalPackage)
            .where(OperationalPackage.task_id == task_id)
            .order_by(OperationalPackage.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()