"""
Retrieval service.

Given a task with:
    - use_case
    - identified requirements
    - extracted entities

Retrieves records from the appropriate sources and persists them to
`retrieved_records`.

Design:
    - Requirements drive retrieval (each requirement has source_hint).
    - Entities filter matching (S-1042, ABC Components, etc.).
    - Deduplication by source_record_id (a record retrieved for one
      requirement is not duplicated for another).
    - Idempotent: existing retrieved_records for the task are cleared
      before re-insertion.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.retrieval import GenericRetriever
from app.repositories import (
    RequirementRepository,
    RetrievedRecordRepository,
    SourceRepository,
    TaskRepository,
)


class RetrievalError(Exception):
    """Raised when retrieval cannot proceed."""

    pass


@dataclass
class RetrievalSummary:
    task_id: UUID
    total_retrieved: int
    requirements_processed: int
    requirements_skipped: int
    sources_used: list[str]


class RetrievalService:
    """Service for retrieving records for a task."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)
        self.req_repo = RequirementRepository(session)
        self.retrieved_repo = RetrievedRecordRepository(session)
        self.source_repo = SourceRepository(session)
        self.retriever = GenericRetriever(session)

    async def retrieve_for_task(self, task_id: UUID) -> RetrievalSummary:
        # 1. Fetch task
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise RetrievalError(f"Task {task_id} not found")
        if not task.use_case:
            raise RetrievalError(
                "Task has no use_case. Run task understanding first."
            )

        # 2. Fetch requirements
        requirements = await self.req_repo.get_by_task_id(task_id)
        if not requirements:
            raise RetrievalError(
                "No requirements found. Run requirement identification first."
            )

        # 3. Extract entities from task metadata
        entities = self._extract_entity_values(task)
        if not entities:
            raise RetrievalError(
                "No entities in task. Retrieval requires entities to match."
            )

        # 4. Load sources by canonical source_key
        sources_by_key = await self.source_repo.get_all_by_source_key()

        # 5. Delete existing retrieved records (idempotent)
        await self.retrieved_repo.delete_by_task_id(task_id)

        # 6. For each requirement, retrieve matching records
        all_rows: list[dict[str, Any]] = []
        seen_source_record_ids: set[UUID] = set()
        requirements_processed = 0
        requirements_skipped = 0
        sources_used: set[str] = set()

        for req in requirements:
            source_key = req.source_hint
            if not source_key:
                requirements_skipped += 1
                continue

            source = sources_by_key.get(source_key)
            if source is None:
                requirements_skipped += 1
                continue

            records = await self.retriever.retrieve(
                source=source,
                entity_values=entities,
            )
            requirements_processed += 1

            for r in records:
                # Dedup: same source_record retrieved for a different requirement
                if r.source_record_id in seen_source_record_ids:
                    continue
                seen_source_record_ids.add(r.source_record_id)

                sources_used.add(r.source_key)
                all_rows.append({
                    "requirement_id": req.id,
                    "source_record_id": r.source_record_id,
                    "retrieval_method": r.retrieval_method,
                    "relevance_score": r.relevance_score,
                    "is_selected": True,
                    "retrieval_metadata": {
                        "source_key": r.source_key,
                        "record_type": r.record_type,
                        "external_id": r.external_id,
                        "match_reason": r.match_reason,
                        "requirement_type": req.requirement_type,
                    },
                })

        # 7. Persist + metadata
        try:
            await self.retrieved_repo.create_many(task_id, all_rows)

            metadata = dict(task.task_metadata or {})
            metadata["retrieval"] = {
                "total_retrieved": len(all_rows),
                "requirements_processed": requirements_processed,
                "requirements_skipped": requirements_skipped,
                "sources_used": sorted(sources_used),
            }
            task.task_metadata = metadata

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return RetrievalSummary(
            task_id=task_id,
            total_retrieved=len(all_rows),
            requirements_processed=requirements_processed,
            requirements_skipped=requirements_skipped,
            sources_used=sorted(sources_used),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_entity_values(task: Task) -> list[str]:
        """
        Extract entity values (strings) from task.task_metadata.understanding.entities.
        """
        metadata = task.task_metadata or {}
        understanding = metadata.get("understanding") or {}
        entities = understanding.get("entities") or []

        values: list[str] = []
        for e in entities:
            if isinstance(e, dict):
                v = e.get("value")
                if isinstance(v, str) and v.strip():
                    values.append(v.strip())
        return values