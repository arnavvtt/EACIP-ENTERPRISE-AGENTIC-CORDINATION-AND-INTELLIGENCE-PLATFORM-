"""
LLM abstraction interface.

This is the ONLY thing EACIP's business logic knows about LLMs.
Every provider (Groq, Gemini, Mock, etc.) implements this interface.

Design principles:
- Minimal surface area (YAGNI).
- Provider-agnostic types (LLMResponse).
- Structured output is the primary use case.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

from app.llm.types import LLMResponse

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    A provider must implement `generate_structured()`.

    Future methods (added only when needed):
    - generate_text()
    - generate_streaming()
    - embed()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name, e.g., 'groq', 'gemini', 'mock'."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> tuple[T, LLMResponse]:
        """
        Generate a structured output matching the given Pydantic schema.

        Args:
            system_prompt: System-level instructions (role, rules).
            user_prompt: The actual user input.
            response_schema: A Pydantic model class. Output will be validated
                             against this. If validation fails, raise
                             LLMInvalidResponseError.
            temperature: 0.0 = deterministic, 1.0 = creative. Default 0.
            max_tokens: Hard cap on output size.

        Returns:
            Tuple of (validated Pydantic instance, raw LLMResponse metadata).

        Raises:
            LLMError: On any provider-level failure.
            LLMInvalidResponseError: If output cannot be parsed/validated.
        """
        ...