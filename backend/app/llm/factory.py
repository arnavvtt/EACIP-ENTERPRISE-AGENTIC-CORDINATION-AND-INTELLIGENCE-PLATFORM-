"""
LLM provider factory.

Returns the appropriate LLMProvider based on application settings.

Usage:
    provider = get_llm_provider()
    result, meta = await provider.generate_structured(...)
"""

from app.config import settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance."""
    provider = settings.llm_provider.lower().strip()

    if provider == "mock":
        return MockLLMProvider()

    if provider == "groq":
        # Imported lazily so that environments without `groq`
        # installed can still run with the mock provider.
        from app.llm.groq_provider import GroqProvider

        return GroqProvider()

    raise ValueError(
        f"Unknown LLM provider: '{provider}'. "
        f"Available: 'mock', 'groq'."
    )