"""
LLM abstraction layer.

Public API:
- LLMProvider            : abstract interface
- MockLLMProvider        : mock provider for development
- GroqProvider           : Groq provider (real LLM)
- get_llm_provider()     : factory based on settings
- LLMResponse            : standard response object
- Errors                 : LLMError, LLMRateLimitError, etc.
"""

from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.llm.mock_provider import MockLLMProvider
from app.llm.types import (
    LLMError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMResponse,
    LLMTimeoutError,
)

__all__ = [
    "LLMProvider",
    "MockLLMProvider",
    "get_llm_provider",
    "LLMResponse",
    "LLMError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMInvalidResponseError",
]

# GroqProvider is intentionally NOT imported at module level
# to keep the mock path lightweight (no groq SDK import unless needed).
# Import explicitly: `from app.llm.groq_provider import GroqProvider`