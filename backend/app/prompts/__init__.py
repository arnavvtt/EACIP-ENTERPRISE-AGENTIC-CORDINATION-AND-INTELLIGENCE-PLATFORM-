"""
Prompt templates for EACIP.

Prompts are separated from service code so they can be:
- Versioned independently
- Reviewed by multiple people
- Swapped per provider or per use case (future)
"""

from app.prompts.task_understanding import (
    build_task_understanding_system_prompt,
    build_task_understanding_user_prompt,
)

__all__ = [
    "build_task_understanding_system_prompt",
    "build_task_understanding_user_prompt",
]