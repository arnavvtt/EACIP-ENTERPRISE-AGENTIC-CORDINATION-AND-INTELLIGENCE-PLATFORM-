"""
Source repository — data access for the `sources` table.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source


class SourceRepository:
    """Repository for the `sources` table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_by_source_key(self) -> dict[str, Source]:
        """
        Return all active sources indexed by source_metadata["source_key"].

        Sources without a source_key are skipped.
        """
        result = await self.session.execute(
            select(Source).where(Source.is_active.is_(True))
        )
        sources = result.scalars().all()

        indexed: dict[str, Source] = {}
        for s in sources:
            key = (s.source_metadata or {}).get("source_key")
            if key:
                indexed[key] = s
        return indexed