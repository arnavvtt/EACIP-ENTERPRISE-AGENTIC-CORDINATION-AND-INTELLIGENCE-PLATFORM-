"""
Policy Ingestion Service (Stage 10.3).

For each policy document (source_record with record_type='policy'):
    1. Extract text from data.content
    2. Chunk it (ChunkingService)
    3. Embed chunks in batch (EmbeddingProvider)
    4. Save to policy_chunks table

Design:
- Idempotent: delete existing chunks for a source_record before re-ingest.
- Batch embedding per document (fewer API calls).
- Transactional: single commit; rollback on failure.
- Provider-agnostic: uses get_embedding_provider().

Only 'policy' record types are ingested. Certificates, emails, POs etc.
are handled by Stage 6 (structured retrieval) and are NOT chunked.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import EmbeddingError, get_embedding_provider
from app.models.source import SourceRecord
from app.repositories import PolicyChunkRepository
from app.services.chunking_service import ChunkingService


class PolicyIngestionError(Exception):
    """Raised when policy ingestion cannot proceed."""

    pass


@dataclass
class IngestionSummary:
    total_documents: int = 0
    total_chunks: int = 0
    documents_skipped: int = 0
    errors: list[str] = field(default_factory=list)


class PolicyIngestionService:
    """Ingests policy documents into policy_chunks with embeddings."""

    # Only these record types are ingested as policy documents
    POLICY_RECORD_TYPE = "policy"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chunk_repo = PolicyChunkRepository(session)
        self.chunker = ChunkingService()

    async def ingest_all_policies(self) -> IngestionSummary:
        """
        Ingest every policy document currently in source_records.

        Idempotent: each document's existing chunks are cleared
        before re-ingestion.
        """
        policies = await self._load_policy_documents()

        summary = IngestionSummary()

        if not policies:
            return summary

        provider = get_embedding_provider()

        try:
            for record in policies:
                await self._ingest_one(record, provider, summary)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return summary

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _load_policy_documents(self) -> list[SourceRecord]:
        result = await self.session.execute(
            select(SourceRecord).where(
                SourceRecord.record_type == self.POLICY_RECORD_TYPE
            )
        )
        return list(result.scalars().all())

    async def _ingest_one(
        self,
        record: SourceRecord,
        provider,
        summary: IngestionSummary,
    ) -> None:
        text = self._extract_text(record)
        if not text:
            summary.documents_skipped += 1
            summary.errors.append(
                f"Skipped {record.external_id}: no text content"
            )
            return

        chunks = self.chunker.chunk_text(text)
        if not chunks:
            summary.documents_skipped += 1
            summary.errors.append(
                f"Skipped {record.external_id}: chunker produced 0 chunks"
            )
            return

        # Embed all chunks of this document in one batch
        chunk_texts = [c.text for c in chunks]
        try:
            vectors, meta = await provider.embed_batch(chunk_texts)
        except EmbeddingError as e:
            summary.documents_skipped += 1
            summary.errors.append(
                f"Embedding failed for {record.external_id}: {e}"
            )
            return

        # Idempotency: clear existing chunks for this document
        await self.chunk_repo.delete_by_source_record_id(record.id)

        # Build rows
        rows: list[dict[str, Any]] = []
        for chunk, vector in zip(chunks, vectors):
            rows.append({
                "source_record_id": record.id,
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.text,
                "embedding": vector,
                "chunk_metadata": {
                    "provider": meta.provider,
                    "model": meta.model,
                    "dimensions": meta.dimensions,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                },
            })

        await self.chunk_repo.create_many(rows)

        summary.total_documents += 1
        summary.total_chunks += len(rows)

    @staticmethod
    def _extract_text(record: SourceRecord) -> str:
        """
        Extract ingestible text from a policy source_record.

        Policies store their body in data.content.
        Title is prepended for better retrieval context.
        """
        data = record.data or {}
        title = str(data.get("title") or "").strip()
        content = str(data.get("content") or "").strip()

        parts = [p for p in (title, content) if p]
        return "\n\n".join(parts)