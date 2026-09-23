"""
Common LLM types used across all providers.

These types are provider-agnostic. Each provider implementation
maps its own internal types to these.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMResponse:
    """
    Standard response from any LLM call.

    Providers must convert their raw response into this shape.
    """

    content: dict[str, Any]
    """Parsed structured output."""

    provider: str
    """Provider name, e.g., 'groq', 'gemini', 'mock'."""

    model: str
    """Specific model used, e.g., 'llama-3.3-70b'."""

    latency_ms: float
    """Time taken in milliseconds."""

    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    raw_response: Optional[Any] = field(default=None, repr=False)
    """Raw provider response, kept for debugging (not repr'd)."""


class LLMError(Exception):
    """Base exception for all LLM-related failures."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when the provider rate-limits us."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when the provider takes too long."""

    pass


class LLMInvalidResponseError(LLMError):
    """Raised when the LLM returns something we can't parse."""

    pass