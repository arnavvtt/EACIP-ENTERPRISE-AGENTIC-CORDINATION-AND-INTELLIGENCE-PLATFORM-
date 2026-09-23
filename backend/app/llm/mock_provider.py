"""
Mock LLM provider.

Implements LLMProvider for development/testing without any real
API calls. Uses simple keyword heuristics to produce plausible
structured outputs. This makes end-to-end demos meaningful while
keeping costs at zero.

When a real provider is integrated later, the rest of the codebase
needs zero changes — just swap this provider via config.
"""

import re
import time
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMProvider
from app.llm.types import (
    LLMError,
    LLMInvalidResponseError,
    LLMResponse,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """
    A deterministic mock LLM provider — TEST FIXTURE ONLY.

    This is NOT production intelligence. Its keyword rules and
    hardcoded use-case list exist ONLY to make development and
    tests meaningful without any real LLM calls.

    IMPORTANT:
        - Production code MUST NOT depend on the hardcoded 5 use cases.
        - Real providers receive valid use cases via `system_prompt`
          (see Stage 4.3), not via built-in domain knowledge.
        - `system_prompt` is intentionally ignored here because this
          is not a real LLM.

    Behavior:
    - For TaskUnderstanding schema: keyword-based heuristics.
    - For any other schema: raises LLMInvalidResponseError.
    - Optionally simulates failure via `simulate_failure=True`.
    """

    def __init__(self, simulate_failure: bool = False) -> None:
        self._simulate_failure = simulate_failure

    @property
    def name(self) -> str:
        return "mock"

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

        # NOTE: system_prompt is intentionally IGNORED by the mock.
        # Real providers will use it (use-case list, output rules, etc.).

        if self._simulate_failure:
            raise LLMError("Simulated LLM failure (for testing)")

        # Dispatch by schema — add more handlers as we go
        schema_name = response_schema.__name__
        if schema_name == "TaskUnderstanding":
            data = self._mock_task_understanding(user_prompt)
        else:
            raise LLMInvalidResponseError(
                f"Mock has no handler for schema '{schema_name}'"
            )

        # Validate against the requested schema
        try:
            validated = response_schema.model_validate(data)
        except ValidationError as e:
            raise LLMInvalidResponseError(
                f"Mock produced invalid output: {e}"
            ) from e

        latency_ms = (time.perf_counter() - start) * 1000

        return validated, LLMResponse(
            content=data,
            provider="mock",
            model="mock-model-v1",
            latency_ms=latency_ms,
            tokens_input=0,
            tokens_output=0,
        )

    # ------------------------------------------------------------------
    # Task Understanding heuristics
    # ------------------------------------------------------------------
    def _mock_task_understanding(self, user_prompt: str) -> dict:
        text = user_prompt.lower()

        use_case = self._infer_use_case(text)
        intent = self._infer_intent(text)
        entities = self._extract_entities(user_prompt)

        return {
            "intent": intent,
            "use_case": use_case,
            "summary": user_prompt.strip()[:200] or "No description provided.",
            "entities": entities,
            "confidence": 0.85,
            "rationale": (
                f"Mock keyword-matching inferred use_case='{use_case}', "
                f"intent='{intent}'."
            ),
        }

    @staticmethod
    def _infer_use_case(text: str) -> str | None:
        """
        TEST-ONLY heuristic.

        These 5 use cases are hardcoded purely for the mock. In
        production, the valid list is injected via system_prompt
        (Stage 4.3), so this heuristic will NOT exist in real
        providers.
        """
        rules = [
            ("supplier_qualification",
             ["supplier", "qualify", "vendor", "onboard", "s-1"]),
            ("purchase_delay",
             ["delay", "shipment", "po-", "purchase", "delayed"]),
            ("incident_investigation",
             ["incident", "outage", "failure", "investigate", "root cause"]),
            ("employee_onboarding",
             ["employee", "new hire", "joining", "onboard"]),
            ("customer_issue",
             ["customer", "complaint", "c-1", "ticket"]),
        ]
        for use_case, keywords in rules:
            if any(k in text for k in keywords):
                return use_case
        return None

    @staticmethod
    def _infer_intent(text: str) -> str:
        intents = [
            ("qualify", "qualify"),
            ("resolve", "resolve"),
            ("investigate", "investigate"),
            ("onboard", "onboard"),
            ("review", "review"),
            ("verify", "verify"),
        ]
        for intent, keyword in intents:
            if keyword in text:
                return intent
        return "process"

    @staticmethod
    def _extract_entities(text: str) -> list[dict]:
        """
        Extract ID-like entities: S-1042, PO-4821, C-1042, QI-101, etc.
        """
        entities: list[dict] = []
        seen: set[str] = set()
        for match in re.finditer(r"\b[A-Z]{1,4}-\d+\b", text):
            value = match.group()
            if value in seen:
                continue
            seen.add(value)
            entities.append({
                "type": "identifier",
                "value": value,
                "confidence": 1.0,
            })
        return entities