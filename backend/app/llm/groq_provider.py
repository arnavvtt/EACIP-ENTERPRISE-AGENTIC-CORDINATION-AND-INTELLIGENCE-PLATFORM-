"""
Groq LLM provider.

Implements LLMProvider using Groq's OpenAI-compatible API with
native Structured Outputs (JSON schema).

Design notes:
- Uses `response_format={"type": "json_schema", "json_schema": {...}}`.
- Schema is generated from the requested Pydantic model via
  `model_json_schema()`.
- Groq-specific errors are mapped to EACIP's LLMError hierarchy.
- No Groq-specific logic leaks into the service layer.
"""

import time
from typing import Type, TypeVar

from groq import AsyncGroq, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.llm.base import LLMProvider
from app.llm.types import (
    LLMError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMResponse,
    LLMTimeoutError,
)

T = TypeVar("T", bound=BaseModel)


class GroqProvider(LLMProvider):
    """
    Groq-backed LLM provider.

    Requires `settings.groq_api_key` to be set.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.groq_api_key
        self._model = model or settings.groq_model

        if not self._api_key:
            raise LLMError(
                "Groq API key is not set. Configure GROQ_API_KEY in .env."
            )

        self._client = AsyncGroq(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "groq"

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> tuple[T, LLMResponse]:
        start = time.perf_counter()

        # Build strict JSON schema from the Pydantic model
        json_schema = {
            "name": response_schema.__name__,
            "strict": True,
            "schema": response_schema.model_json_schema(),
        }

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": json_schema,
                },
            )
        except RateLimitError as e:
            raise LLMRateLimitError(f"Groq rate limit exceeded: {e}") from e
        except APITimeoutError as e:
            raise LLMTimeoutError(f"Groq request timed out: {e}") from e
        except APIError as e:
            raise LLMError(f"Groq API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected Groq failure: {e}") from e

        # Extract the raw content
        choice = completion.choices[0]
        raw_content = choice.message.content
        if not raw_content:
            raise LLMInvalidResponseError("Groq returned empty content.")

        # Parse & validate
        try:
            validated = response_schema.model_validate_json(raw_content)
        except ValidationError as e:
            raise LLMInvalidResponseError(
                f"Groq output failed schema validation: {e}"
            ) from e

        latency_ms = (time.perf_counter() - start) * 1000

        usage = getattr(completion, "usage", None)
        tokens_input = getattr(usage, "prompt_tokens", None) if usage else None
        tokens_output = getattr(usage, "completion_tokens", None) if usage else None

        return validated, LLMResponse(
            content=validated.model_dump(),
            provider="groq",
            model=self._model,
            latency_ms=latency_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            raw_response=None,
        )