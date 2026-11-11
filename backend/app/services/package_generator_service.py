"""
Package Generator Service.
Assembles the 11 structured sections of the Operational Package.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import get_llm_provider
from app.repositories import (
    RequirementRepository,
    RetrievedRecordRepository,
    CorrelationRepository,
    ValidationRepository,
    PackageRepository,
    TaskRepository,
)
from app.prompts.package_insights import (
    PACKAGE_INSIGHTS_SYSTEM_PROMPT,
    PackageInsightsOutput,
    build_package_insights_prompt,
)


class PackageGeneratorError(Exception):
    """Raised when package generation fails."""
    pass


class PackageGeneratorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)
        self.req_repo = RequirementRepository(session)
        self.ret_repo = RetrievedRecordRepository(session)
        self.corr_repo = CorrelationRepository(session)
        self.val_repo = ValidationRepository(session)
        self.pkg_repo = PackageRepository(session)

    async def generate_for_task(self, task_id: UUID) -> dict[str, Any]:
        # 1. Fetch all data
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise PackageGeneratorError("Task not found.")

        requirements = await self.req_repo.get_by_task_id(task_id)
        retrieved = await self.ret_repo.get_by_task_id(task_id)
        correlations = await self.corr_repo.get_by_task_id(task_id)
        validations = await self.val_repo.get_by_task_id(task_id)

        if not requirements:
            raise PackageGeneratorError("Cannot generate package: No requirements found.")

        gaps = self._build_gaps(validations)
        inconsistencies = self._build_inconsistencies(validations)

        # 2. Assemble Sections (Deterministic)
        sections = {
            "section_1_task_summary": {"task_id": str(task_id), "title": task.title, "use_case": task.use_case},
            "section_2_relevant_entities": self._build_entities(task),
            "section_3_required_context": self._build_requirements(requirements),
            "section_4_retrieved_information": self._build_retrieved(retrieved),
            "section_5_correlated_information": self._build_correlations(correlations),
            "section_6_historical_context": {"note": "Not implemented yet in prototype."},
            "section_7_information_gaps": gaps,
            "section_8_potential_inconsistencies": inconsistencies,
            "section_9_relevant_policies": {"note": "Policy chunks will be integrated here."},
            "section_10_source_traceability": self._build_traceability(retrieved),
        }

        # 3. Section 11: AI Insights (LLM)
        insights_data = {"note": "LLM generation failed or skipped."}
        try:
            llm = get_llm_provider()
            prompt = build_package_insights_prompt(
                task_title=task.title,
                use_case=task.use_case or "unknown",
                gaps=gaps,
                inconsistencies=inconsistencies,
                correlations=correlations,
            )
            
            # Calling generate_structured instead of generate_text
            validated_output, llm_meta = await llm.generate_structured(
                system_prompt=PACKAGE_INSIGHTS_SYSTEM_PROMPT,
                user_prompt=prompt,
                response_schema=PackageInsightsOutput,
            )
            
            insights_data = validated_output.model_dump()
            # Add meta info
            insights_data["_meta"] = {
                "provider": llm_meta.provider,
                "model": llm_meta.model,
                "latency_ms": llm_meta.latency_ms
            }

        except Exception as e:
            insights_data = {"error": str(e), "note": "Could not generate AI insights."}

        sections["section_11_ai_insights_and_next_steps"] = insights_data

        # 4. Save to Database
        pkg = await self.pkg_repo.create(
            task_id=task_id,
            sections=sections,
            summary="Package generated with AI insights."
        )
        
        await self.session.commit()
        
        return {
            "package_id": pkg.id,
            "version": pkg.version,
            "status": pkg.status,
            "sections_count": len(sections)
        }

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------
    def _build_entities(self, task) -> list:
        if task.task_metadata and "understanding" in task.task_metadata:
            return task.task_metadata["understanding"].get("entities", [])
        return []

    def _build_requirements(self, requirements) -> list:
        return [{"id": str(r.id), "type": r.requirement_type, "mandatory": r.is_mandatory} for r in requirements]

    def _build_retrieved(self, records) -> list:
        return [{"record_id": str(r.source_record_id), "method": r.retrieval_method, "score": r.relevance_score} for r in records]

    def _build_correlations(self, correlations) -> list:
        return [{"source_a": str(c.record_a_id), "source_b": str(c.record_b_id), "type": c.relationship_type, "basis": c.basis} for c in correlations]

    def _build_gaps(self, validations) -> list:
        return [{"type": v.validation_type, "severity": v.severity, "description": v.description, "details": v.details} for v in validations if v.validation_type == "missing_requirement"]

    def _build_inconsistencies(self, validations) -> list:
        return [{"type": v.validation_type, "severity": v.severity, "description": v.description, "details": v.details} for v in validations if v.validation_type == "inconsistency"]

    def _build_traceability(self, records) -> list:
        return [{"record_id": str(r.source_record_id), "retrieved_at": str(r.created_at)} for r in records]