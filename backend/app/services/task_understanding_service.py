"""
Task Understanding service.

Orchestrates:
    1. Fetch task
    2. Call LLM provider
    3. Save structured understanding back to the task
    4. Return the updated task

Transaction boundary lives here (service layer), as per EACIP architecture.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import LLMError, get_llm_provider
from app.models.task import Task
from app.prompts import (
    build_task_understanding_system_prompt,
    build_task_understanding_user_prompt,
)
from app.repositories import TaskRepository
from app.schemas.task_understanding import TaskUnderstanding


class TaskUnderstandingError(Exception):
    """Raised when task understanding fails."""

    pass


class TaskNotFoundError(TaskUnderstandingError):
    """Raised when the task doesn't exist."""

    pass


class TaskUnderstandingService:
    """Service for understanding operational tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TaskRepository(session)

    async def understand_task(self, task_id: UUID) -> Task:
        """
        Run task understanding and persist the result.

        Steps:
        1. Fetch task (raise if not found)
        2. Call LLM provider with task text
        3. Update task.intent, task.use_case, task.task_metadata
        4. Commit and return
        """
        # 1. Fetch task
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # 2. Call LLM
        provider = get_llm_provider()
        user_prompt = build_task_understanding_user_prompt(
            title=task.title,
            description=task.description,
            use_case_hint=task.use_case,
        )

        try:
            understanding, meta = await provider.generate_structured(
                system_prompt=build_task_understanding_system_prompt(),
                user_prompt=user_prompt,
                response_schema=TaskUnderstanding,
                temperature=0.0,
            )
        except LLMError as e:
            raise TaskUnderstandingError(f"LLM call failed: {e}") from e

        # 3. Persist understanding
        self._apply_understanding(task, understanding, meta)

        await self.session.commit()
        await self.session.refresh(task)
        return task

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _apply_understanding(
        self,
        task: Task,
        understanding: TaskUnderstanding,
        meta,
    ) -> None:
        """
        Merge the LLM understanding into the task.

        - intent / use_case: overwrite with LLM output
        - task_metadata: keep prior fields, add an "understanding" block
        - task_metadata["user_provided_use_case"]: preserve the original
          hint for audit (LLM output becomes authoritative).
        """
        metadata = dict(task.task_metadata or {})
        if task.use_case and "user_provided_use_case" not in metadata:
            metadata["user_provided_use_case"] = task.use_case

        metadata["understanding"] = {
            "summary": understanding.summary,
            "entities": [e.model_dump() for e in understanding.entities],
            "confidence": understanding.confidence,
            "rationale": understanding.rationale,
            "provider": meta.provider,
            "model": meta.model,
            "latency_ms": meta.latency_ms,
        }

        task.intent = understanding.intent
        task.use_case = understanding.use_case
        task.task_metadata = metadata