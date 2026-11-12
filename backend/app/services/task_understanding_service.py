"""
Task Understanding Service (Stage 4).
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import get_llm_provider
from app.llm.types import LLMError
from app.models.task import Task
from app.prompts import (
    build_task_understanding_system_prompt,
    build_task_understanding_user_prompt,
)
from app.repositories import TaskRepository
from app.schemas.task_understanding import TaskUnderstanding


class TaskNotFoundError(Exception):
    """Raised when the requested task does not exist."""
    pass


class TaskUnderstandingError(Exception):
    """Raised when task understanding fails."""
    pass


class TaskUnderstandingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)

    async def understand_task(self, task_id: UUID) -> Task:
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")

        provider = get_llm_provider()
        
        system_prompt = build_task_understanding_system_prompt()
        # FIX: Removed 'provided_use_case' argument as the function doesn't accept it
        user_prompt = build_task_understanding_user_prompt(
            title=task.title,
            description=task.description,
        )

        try:
            understanding, meta = await provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=TaskUnderstanding,
                temperature=0.0,
                max_tokens=1024,
            )
        except LLMError as e:
            raise TaskUnderstandingError(str(e)) from e

        # ==========================================
        # CRITICAL FIX: Respect user's explicit use_case
        # ==========================================
        final_use_case = task.use_case
        if not final_use_case:
            # Only use the LLM's inference if user didn't provide one
            final_use_case = understanding.use_case
            
        task.intent = understanding.intent
        task.use_case = final_use_case
        
        # Update metadata
        metadata = dict(task.task_metadata or {})
        metadata["understanding"] = {
            "summary": understanding.summary,
            "confidence": understanding.confidence,
            "rationale": understanding.rationale,
            "provider": meta.provider,
            "model": meta.model,
            "latency_ms": meta.latency_ms,
            "entities": [e.model_dump() for e in understanding.entities],
        }
        task.task_metadata = metadata

        await self.session.commit()
        await self.session.refresh(task)
        return task