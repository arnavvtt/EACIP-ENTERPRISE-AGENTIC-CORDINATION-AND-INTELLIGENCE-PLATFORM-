"""
Human Review repository.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.human_review import HumanReview


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        task_id: UUID,
        package_id: UUID,
        decision: str,
        comments: Optional[str] = None,
    ) -> HumanReview:
        review = HumanReview(
            task_id=task_id,
            package_id=package_id,
            decision=decision,
            comments=comments,
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def get_by_package_id(self, package_id: UUID) -> Optional[HumanReview]:
        stmt = select(HumanReview).where(HumanReview.package_id == package_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()