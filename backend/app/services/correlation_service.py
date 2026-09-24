"""
Correlation service.

Given a task with retrieved records, runs the correlation engine and
persists the resulting correlations.

Idempotent: deletes existing correlations for the task before
insertion, in a single transaction with rollback on failure.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.correlation.engine import run_correlation_engine
from app.correlation.types import EntityRef
from app.models.source import SourceRecord
from app.models.task import Task
from app.repositories import (
    CorrelationRepository,
    RetrievedRecordRepository,
    TaskRepository,
)


class CorrelationError(Exception):
    """Raised when correlation cannot proceed."""

    pass


@dataclass
class CorrelationSummary:
    task_id: UUID
    total_correlations: int
    anchor_external_id: str | None
    basis_breakdown: dict[str, int] = field(default_factory=dict)


class CorrelationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)
        self.retrieved_repo = RetrievedRecordRepository(session)
        self.correlation_repo = CorrelationRepository(session)

    async def correlate_for_task(self, task_id: UUID) -> CorrelationSummary:
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise CorrelationError(f"Task {task_id} not found")
        if not task.use_case:
            raise CorrelationError(
                "Task has no use_case. Run task understanding first."
            )

        retrieved = await self.retrieved_repo.get_by_task_id(task_id)
        if not retrieved:
            raise CorrelationError(
                "No retrieved records. Run retrieval first."
            )

        source_record_ids = [r.source_record_id for r in retrieved]
        result = await self.session.execute(
            select(SourceRecord).where(SourceRecord.id.in_(source_record_ids))
        )
        records = list(result.scalars().all())

        entities = self._extract_entities(task)
        if not entities:
            raise CorrelationError(
                "No entities in task. Cannot resolve anchor."
            )

        engine_result = run_correlation_engine(
            use_case=task.use_case,
            entities=entities,
            records=records,
        )

        rows: list[dict[str, Any]] = []
        for c in engine_result.correlations:
            rows.append({
                "record_a_id": c.record_a_id,
                "record_b_id": c.record_b_id,
                "relationship_type": c.relationship_type,
                "basis": c.basis,
                "confidence": c.confidence,
                "correlation_metadata": c.metadata,
            })

        try:
            await self.correlation_repo.delete_by_task_id(task_id)
            await self.correlation_repo.create_many(task_id, rows)

            breakdown: dict[str, int] = {}
            for c in engine_result.correlations:
                breakdown[c.basis] = breakdown.get(c.basis, 0) + 1

            metadata = dict(task.task_metadata or {})
            metadata["correlation"] = {
                "total_correlations": len(rows),
                "anchor_external_id": (
                    engine_result.anchor.record_external_id
                    if engine_result.anchor else None
                ),
                "basis_breakdown": breakdown,
            }
            task.task_metadata = metadata

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        breakdown: dict[str, int] = {}
        for c in engine_result.correlations:
            breakdown[c.basis] = breakdown.get(c.basis, 0) + 1

        return CorrelationSummary(
            task_id=task_id,
            total_correlations=len(rows),
            anchor_external_id=(
                engine_result.anchor.record_external_id
                if engine_result.anchor else None
            ),
            basis_breakdown=breakdown,
        )

    @staticmethod
    def _extract_entities(task: Task) -> list[EntityRef]:
        metadata = task.task_metadata or {}
        understanding = metadata.get("understanding") or {}
        raw = understanding.get("entities") or []
        out: list[EntityRef] = []
        for e in raw:
            if not isinstance(e, dict):
                continue
            t = e.get("type")
            v = e.get("value")
            c = e.get("confidence", 0.0)
            if isinstance(t, str) and isinstance(v, str) and v.strip():
                out.append(EntityRef(
                    type=t,
                    value=v.strip(),
                    confidence=float(c) if isinstance(c, (int, float)) else 0.0,
                ))
        return out