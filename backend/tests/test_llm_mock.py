"""
Tests for MockLLMProvider.

Verifies:
- Task Understanding heuristics (use_case, intent, entities)
- Deterministic behavior
- Failure simulation
- Schema validation errors
"""

import pytest

from app.llm.mock_provider import MockLLMProvider
from app.llm.types import LLMError, LLMInvalidResponseError
from app.schemas.task_understanding import TaskUnderstanding


@pytest.mark.asyncio
async def test_mock_supplier_task():
    p = MockLLMProvider()
    r, meta = await p.generate_structured(
        system_prompt="(ignored)",
        user_prompt="Qualify ABC Components S-1042 as supplier",
        response_schema=TaskUnderstanding,
    )
    assert r.intent == "qualify"
    assert r.use_case == "supplier_qualification"
    assert any(e.value == "S-1042" for e in r.entities)
    assert meta.provider == "mock"
    assert meta.model == "mock-model-v1"


@pytest.mark.asyncio
async def test_mock_delay_task():
    p = MockLLMProvider()
    r, _ = await p.generate_structured(
        system_prompt="",
        user_prompt="Critical shipment PO-4821 is delayed",
        response_schema=TaskUnderstanding,
    )
    assert r.intent == "process"
    assert r.use_case == "purchase_delay"


@pytest.mark.asyncio
async def test_mock_incident_task():
    p = MockLLMProvider()
    r, _ = await p.generate_structured(
        system_prompt="",
        user_prompt="Investigate payment failure incident",
        response_schema=TaskUnderstanding,
    )
    assert r.intent == "investigate"
    assert r.use_case == "incident_investigation"


@pytest.mark.asyncio
async def test_mock_unknown_task():
    p = MockLLMProvider()
    r, _ = await p.generate_structured(
        system_prompt="",
        user_prompt="Random unrelated text xyz",
        response_schema=TaskUnderstanding,
    )
    assert r.use_case is None


@pytest.mark.asyncio
async def test_mock_failure_simulation():
    p = MockLLMProvider(simulate_failure=True)
    with pytest.raises(LLMError):
        await p.generate_structured(
            system_prompt="",
            user_prompt="test",
            response_schema=TaskUnderstanding,
        )


@pytest.mark.asyncio
async def test_mock_unknown_schema():
    from pydantic import BaseModel

    class OtherSchema(BaseModel):
        field: str

    p = MockLLMProvider()
    with pytest.raises(LLMInvalidResponseError):
        await p.generate_structured(
            system_prompt="",
            user_prompt="test",
            response_schema=OtherSchema,
        )


@pytest.mark.asyncio
async def test_mock_entity_extraction():
    p = MockLLMProvider()
    r, _ = await p.generate_structured(
        system_prompt="",
        user_prompt="Check supplier S-1042, PO-4821, and QI-101",
        response_schema=TaskUnderstanding,
    )
    values = [e.value for e in r.entities]
    assert "S-1042" in values
    assert "PO-4821" in values
    assert "QI-101" in values
    # All three should be unique (no duplicates)
    assert len(values) == len(set(values))