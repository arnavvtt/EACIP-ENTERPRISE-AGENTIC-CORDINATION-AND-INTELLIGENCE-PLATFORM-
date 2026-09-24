"""
Requirement Identification service (Stage 5).

Orchestrates:
    1. Fetch task (must have use_case)
    2. Load registry baseline for the use_case
    3. Ask LLM for at most N task-specific candidates
    4. Deterministic validation + merge
    5. Persist final requirements (with rollback on failure)
    6. Log rejected candidates + identification metadata in task.task_metadata

The registry is AUTHORITATIVE. LLM candidates are validated and
downgraded (is_mandatory always False for LLM-only requirements).
Source hints for LLM-accepted requirements come from a deterministic
map (app.requirement_taxonomy.DEFAULT_SOURCE_HINT), NOT from the LLM.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm import (
    LLMError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMTimeoutError,
    get_llm_provider,
)
from app.models.task import Task
from app.prompts import (
    build_requirement_system_prompt,
    build_requirement_user_prompt,
)
from app.requirement_registry import (
    RegistryRequirement,
    get_allowed_types_for_use_case,
    get_baseline,
)
from app.requirement_taxonomy import (
    get_default_source_hint,
    is_valid_type,
)
from app.repositories import RequirementRepository, TaskRepository
from app.schemas.requirement import (
    RequirementCandidate,
    RequirementCandidatesOutput,
)


class RequirementError(Exception):
    """Raised on any requirement-identification failure."""

    pass


class RequirementService:
    """Service for identifying task requirements."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)
        self.requirement_repo = RequirementRepository(session)

    async def identify_requirements(self, task_id: UUID) -> Task:
        """
        Identify and persist requirements for a task.

        Steps:
        1. Fetch task; must have use_case
        2. Load registry baseline
        3. Call LLM for candidates (failures are non-fatal → baseline-only)
        4. Validate + merge
        5. Persist (delete existing, insert new) — with rollback on failure
        6. Update task metadata with identification summary
        """
        # 1. Fetch task
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise RequirementError(f"Task {task_id} not found")

        if not task.use_case:
            raise RequirementError(
                "Task has no use_case. Run task understanding first."
            )

        # 2. Load registry baseline
        entry = get_baseline(task.use_case)
        if entry is None:
            raise RequirementError(
                f"No registry entry for use_case '{task.use_case}'."
            )

        baseline = entry.requirements
        allowed_types = get_allowed_types_for_use_case(task.use_case)

        # 3. Ask LLM for candidates (failures are non-fatal)
        candidates, llm_meta, llm_status, llm_error_type = (
            await self._get_llm_candidates(
                task=task,
                baseline=baseline,
                allowed_types=allowed_types,
            )
        )

        # 4. Deterministic validation + merge
        accepted_rows, rejected = self._merge(
            baseline=baseline,
            candidates=candidates,
            allowed_types=allowed_types,
            use_case=task.use_case,
        )

        # 5-6. Persist + metadata, in a single transaction with rollback
        try:
            await self.requirement_repo.delete_by_task_id(task_id)
            await self.requirement_repo.create_many(task_id, accepted_rows)

            await self._record_identification_metadata(
                task=task,
                llm_meta=llm_meta,
                llm_status=llm_status,
                llm_error_type=llm_error_type,
                total_candidates=len(candidates),
                accepted_from_llm=sum(
                    1 for r in accepted_rows
                    if r["requirement_metadata"].get("provenance")
                    == "llm_candidate"
                ),
                rejected=rejected,
            )

            await self.session.commit()
            await self.session.refresh(task)
            return task
        except Exception:
            await self.session.rollback()
            raise

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    async def _get_llm_candidates(
        self,
        *,
        task: Task,
        baseline: tuple[RegistryRequirement, ...],
        allowed_types: tuple[str, ...],
    ) -> tuple[list[RequirementCandidate], Any, str, str | None]:
        """
        Call LLM for candidate suggestions.

        Returns:
            (candidates, llm_meta, llm_status, error_type)

        llm_status:
            - "success" : LLM responded successfully (candidates may be
                          empty — that is a valid response too)
            - "failed"  : LLM raised an error; pipeline proceeds with
                          baseline only
        error_type:
            - None on success
            - "rate_limit"       | "timeout"
            - "invalid_response" | "provider_error"
        """
        provider = get_llm_provider()
        system_prompt = build_requirement_system_prompt(
            allowed_types=allowed_types,
            max_candidates=settings.llm_max_requirement_candidates,
        )
        entities = (task.task_metadata or {}).get("understanding", {}).get(
            "entities"
        )
        user_prompt = build_requirement_user_prompt(
            title=task.title,
            description=task.description,
            use_case=task.use_case or "",
            intent=task.intent,
            entities=entities,
            baseline=baseline,
        )

        try:
            output, meta = await provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=RequirementCandidatesOutput,
                temperature=0.0,
                max_tokens=1024,
            )
            return output.candidates, meta, "success", None
        except LLMRateLimitError:
            return [], None, "failed", "rate_limit"
        except LLMTimeoutError:
            return [], None, "failed", "timeout"
        except LLMInvalidResponseError:
            return [], None, "failed", "invalid_response"
        except LLMError:
            return [], None, "failed", "provider_error"

    # ------------------------------------------------------------------
    # Deterministic merge (5 rules)
    # ------------------------------------------------------------------
    def _merge(
        self,
        *,
        baseline: tuple[RegistryRequirement, ...],
        candidates: list[RequirementCandidate],
        allowed_types: tuple[str, ...],
        use_case: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Merge baseline (authoritative) + validated LLM candidates.

        Returns: (accepted_rows, rejected_candidates)
        """
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        # Baseline first (authoritative)
        seen_types: set[str] = set()
        for r in baseline:
            accepted.append({
                "requirement_type": r.requirement_type,
                "description": r.description,
                "is_mandatory": r.is_mandatory,
                "source_hint": r.source_hint,
                "priority": r.priority,
                "requirement_metadata": {
                    "provenance": "registry",
                    "source_registry": use_case,
                    "task_specificity": "generic",
                    "validation_status": "accepted",
                },
            })
            seen_types.add(r.requirement_type)

        next_priority = max((r.priority for r in baseline), default=0) + 1
        threshold = settings.llm_requirement_confidence_threshold

        for c in candidates:
            # Rule 1: type must be in taxonomy
            if not is_valid_type(c.requirement_type):
                rejected.append(self._reject(c, "unknown_requirement_type"))
                continue

            # Rule 2: confidence threshold
            if c.confidence < threshold:
                rejected.append(self._reject(c, "low_confidence"))
                continue

            # Rule 3: deduplication against baseline
            if c.requirement_type in seen_types:
                rejected.append(self._reject(c, "already_in_baseline"))
                continue

            # Rule 4: non-empty description
            if not c.description.strip():
                rejected.append(self._reject(c, "empty_description"))
                continue

            # Rule 5: must be allowed for this use case (cross-domain block)
            if c.requirement_type not in allowed_types:
                rejected.append(self._reject(c, "not_relevant_to_use_case"))
                continue

            # Accepted — source_hint comes from deterministic map, not LLM
            source_hint = get_default_source_hint(c.requirement_type)
            accepted.append({
                "requirement_type": c.requirement_type,
                "description": c.description,
                "is_mandatory": False,  # LLM-only never mandatory
                "source_hint": source_hint,
                "priority": next_priority,
                "requirement_metadata": {
                    "provenance": "llm_candidate",
                    "llm_confidence": c.confidence,
                    "llm_rationale": c.rationale,
                    "validation_status": "accepted",
                    "task_specificity": "task_specific",
                    "source_hint_source": "deterministic_map",
                },
            })
            seen_types.add(c.requirement_type)
            next_priority += 1

        return accepted, rejected

    @staticmethod
    def _reject(c: RequirementCandidate, reason: str) -> dict[str, Any]:
        return {
            "requirement_type": c.requirement_type,
            "description": c.description,
            "confidence": c.confidence,
            "reason": reason,
        }

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    async def _record_identification_metadata(
        self,
        *,
        task: Task,
        llm_meta: Any,
        llm_status: str,
        llm_error_type: str | None,
        total_candidates: int,
        accepted_from_llm: int,
        rejected: list[dict[str, Any]],
    ) -> None:
        metadata = dict(task.task_metadata or {})
        metadata["requirement_identification"] = {
            "llm_status": llm_status,             # "success" | "failed"
            "llm_error_type": llm_error_type,     # None | category
            "provider": llm_meta.provider if llm_meta else None,
            "model": llm_meta.model if llm_meta else None,
            "latency_ms": llm_meta.latency_ms if llm_meta else None,
            "candidates_suggested": total_candidates,
            "candidates_accepted": accepted_from_llm,
            "candidates_rejected": len(rejected),
            "rejected_candidates": rejected,
        }
        task.task_metadata = metadata