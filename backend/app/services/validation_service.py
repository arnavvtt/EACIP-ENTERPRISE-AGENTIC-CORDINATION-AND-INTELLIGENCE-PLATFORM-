"""
Validation service (Stage 9).

Detects two kinds of findings:
    1. Gaps — requirements with zero retrieved records
    2. Inconsistencies — same field, different values across correlated records

Design:
- Idempotent: delete existing validations for the task before insert.
- Transactional: single commit; rollback on any failure.
- Deterministic: no fuzzy matching, no LLM.
- Config-driven: comparable fields + severity live in validation_rules.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import SourceRecord
from app.models.task import Task
from app.repositories import (
    CorrelationRepository,
    RequirementRepository,
    RetrievedRecordRepository,
    TaskRepository,
    ValidationRepository,
)
from app.validation_rules import (
    COMPARABLE_FIELDS,
    GAP_SEVERITY_MANDATORY,
    GAP_SEVERITY_OPTIONAL,
    INCONSISTENCY_SEVERITY,
)


class ValidationError(Exception):
    """Raised when validation cannot proceed."""

    pass


@dataclass
class ValidationSummary:
    task_id: UUID
    total_gaps: int
    total_inconsistencies: int
    by_severity: dict[str, int] = field(default_factory=dict)


class ValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)
        self.req_repo = RequirementRepository(session)
        self.retrieved_repo = RetrievedRecordRepository(session)
        self.corr_repo = CorrelationRepository(session)
        self.validation_repo = ValidationRepository(session)

    async def validate_for_task(self, task_id: UUID) -> ValidationSummary:
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValidationError(f"Task {task_id} not found")
        if not task.use_case:
            raise ValidationError(
                "Task has no use_case. Run task understanding first."
            )

        requirements = await self.req_repo.get_by_task_id(task_id)
        retrieved = await self.retrieved_repo.get_by_task_id(task_id)
        correlations = await self.corr_repo.get_by_task_id(task_id)

        source_key_by_record = {
            rr.source_record_id: (rr.retrieval_metadata or {}).get(
                "source_key", "unknown"
            )
            for rr in retrieved
        }

        # Load source records referenced by correlations
        record_ids: set[UUID] = set()
        for c in correlations:
            record_ids.add(c.record_a_id)
            record_ids.add(c.record_b_id)

        records_by_id: dict[UUID, SourceRecord] = {}
        if record_ids:
            result = await self.session.execute(
                select(SourceRecord).where(SourceRecord.id.in_(record_ids))
            )
            records_by_id = {r.id: r for r in result.scalars().all()}

        gaps = self._detect_gaps(requirements, retrieved)
        inconsistencies = self._detect_inconsistencies(
            correlations, records_by_id, source_key_by_record
        )

        all_rows = gaps + inconsistencies

        try:
            await self.validation_repo.delete_by_task_id(task_id)
            await self.validation_repo.create_many(task_id, all_rows)

            by_severity: dict[str, int] = defaultdict(int)
            for row in all_rows:
                by_severity[row["severity"]] += 1

            metadata = dict(task.task_metadata or {})
            metadata["validation"] = {
                "total_gaps": len(gaps),
                "total_inconsistencies": len(inconsistencies),
                "by_severity": dict(by_severity),
            }
            task.task_metadata = metadata

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return ValidationSummary(
            task_id=task_id,
            total_gaps=len(gaps),
            total_inconsistencies=len(inconsistencies),
            by_severity=dict(by_severity),
        )

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_gaps(requirements, retrieved) -> list[dict[str, Any]]:
        counts: dict[UUID, int] = defaultdict(int)
        for rr in retrieved:
            if rr.requirement_id is not None:
                counts[rr.requirement_id] += 1

        rows: list[dict[str, Any]] = []
        for req in requirements:
            if counts.get(req.id, 0) == 0:
                severity = (
                    GAP_SEVERITY_MANDATORY
                    if req.is_mandatory
                    else GAP_SEVERITY_OPTIONAL
                )
                label = "Required" if req.is_mandatory else "Optional"
                rows.append({
                    "requirement_id": req.id,
                    "validation_type": "missing_requirement",
                    "severity": severity,
                    "description": (
                        f"{label} information missing: {req.requirement_type}"
                    ),
                    "details": {
                        "requirement_type": req.requirement_type,
                        "source_hint": req.source_hint,
                        "retrieved_count": 0,
                    },
                    "status": "open",
                })
        return rows

    @staticmethod
    def _detect_inconsistencies(
        correlations,
        records_by_id: dict[UUID, SourceRecord],
        source_key_by_record: dict[UUID, str],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for c in correlations:
            rec_a = records_by_id.get(c.record_a_id)
            rec_b = records_by_id.get(c.record_b_id)
            if rec_a is None or rec_b is None:
                continue

            a_fields = set(COMPARABLE_FIELDS.get(rec_a.record_type, ()))
            b_fields = set(COMPARABLE_FIELDS.get(rec_b.record_type, ()))
            common = a_fields & b_fields
            if not common:
                continue

            a_data = rec_a.data or {}
            b_data = rec_b.data or {}

            conflicts: list[dict[str, Any]] = []
            for f in sorted(common):
                va = a_data.get(f)
                vb = b_data.get(f)
                if va is None or vb is None:
                    continue
                if str(va).strip() == str(vb).strip():
                    continue
                conflicts.append({
                    "field": f,
                    "value_a": str(va),
                    "value_b": str(vb),
                })

            if not conflicts:
                continue

            if len(conflicts) == 1:
                cf = conflicts[0]
                desc = (
                    f"Potential inconsistency detected: {cf['field']} "
                    f"({cf['value_a']} vs {cf['value_b']}) — human verification required"
                )
            else:
                field_list = ", ".join(cf["field"] for cf in conflicts)
                desc = (
                    f"Potential inconsistencies detected in {len(conflicts)} fields "
                    f"({field_list}) — human verification required"
                )

            detail_conflicts = []
            for cf in conflicts:
                detail_conflicts.append({
                    "field": cf["field"],
                    "values": [
                        {
                            "record_id": str(rec_a.id),
                            "external_id": rec_a.external_id,
                            "source_key": source_key_by_record.get(
                                rec_a.id, "unknown"
                            ),
                            "value": cf["value_a"],
                        },
                        {
                            "record_id": str(rec_b.id),
                            "external_id": rec_b.external_id,
                            "source_key": source_key_by_record.get(
                                rec_b.id, "unknown"
                            ),
                            "value": cf["value_b"],
                        },
                    ],
                })

            rows.append({
                "requirement_id": None,
                "validation_type": "inconsistency",
                "severity": INCONSISTENCY_SEVERITY,
                "description": desc,
                "details": {
                    "conflict_count": len(conflicts),
                    "conflicts": detail_conflicts,
                },
                "status": "open",
            })
        return rows