"""
PolicyChunk repository — data access for `policy_chunks` table.

No commit — caller (service) owns the transaction.

Notes:
- Chunks are usually inserted in bulk during ingestion.
- Deletion by source_record_id is the common re-ingest pattern.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_chunk import PolicyChunk


class PolicyChunkRepository:
    """Repository for the `policy_chunks` table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(
        self,
        rows: list[dict[str, Any]],
    ) -> list[PolicyChunk]:
        """
        Bulk insert policy chunks.

        Each row dict must contain:
            source_record_id, chunk_index, chunk_text,
            embedding, chunk_metadata
        """
        created: list[PolicyChunk] = []
        for row in rows:
            chunk = PolicyChunk(
                source_record_id=row["source_record_id"],
                chunk_index=row["chunk_index"],
                chunk_text=row["chunk_text"],
                embedding=row["embedding"],
                chunk_metadata=row.get("chunk_metadata", {}),
            )
            self.session.add(chunk)
            created.append(chunk)
        await self.session.flush()
        return created

    async def delete_by_source_record_id(
        self, source_record_id: UUID
    ) -> int:
        """Delete all chunks for a source record. Returns count."""
        result = await self.session.execute(
            delete(PolicyChunk).where(
                PolicyChunk.source_record_id == source_record_id
            )
        )
        return result.rowcount or 0

    async def get_by_source_record_id(
        self, source_record_id: UUID
    ) -> list[PolicyChunk]:
        """Return chunks for a source record, ordered by chunk_index."""
        result = await self.session.execute(
            select(PolicyChunk)
            .where(PolicyChunk.source_record_id == source_record_id)
            .order_by(PolicyChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return total number of policy chunks."""
        result = await self.session.execute(
            select(func.count()).select_from(PolicyChunk)
        )
        return result.scalar_one()

    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[PolicyChunk]:
        """Return a paginated list of all chunks."""
        result = await self.session.execute(
            select(PolicyChunk)
            .order_by(PolicyChunk.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())