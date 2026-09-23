"""
Tests for TaskUnderstanding / ExtractedEntity schemas.

Verifies strict-mode compatibility and validation rules.
"""

import pytest
from pydantic import ValidationError

from app.schemas.task_understanding import ExtractedEntity, TaskUnderstanding


def test_schema_required_fields():
    """All fields must be present (strict mode requirement)."""
    s = TaskUnderstanding.model_json_schema()
    required = set(s.get("required", []))
    assert required == {
        "intent",
        "use_case",
        "summary",
        "entities",
        "confidence",
        "rationale",
    }


def test_schema_additional_properties_false():
    """Strict mode requires additionalProperties: false."""
    s = TaskUnderstanding.model_json_schema()
    assert s.get("additionalProperties") is False


def test_nested_schema_additional_properties_false():
    s = TaskUnderstanding.model_json_schema()
    ee = s["$defs"]["ExtractedEntity"]
    assert ee.get("additionalProperties") is False


def test_no_default_keyword_in_schema():
    """Strict mode rejects `default` keywords."""
    s = TaskUnderstanding.model_json_schema()
    # no `default` keys anywhere
    def has_default(obj):
        if isinstance(obj, dict):
            if "default" in obj:
                return True
            return any(has_default(v) for v in obj.values())
        if isinstance(obj, list):
            return any(has_default(x) for x in obj)
        return False
    assert not has_default(s)


def test_valid_full_task_understanding():
    t = TaskUnderstanding(
        intent="qualify",
        use_case="supplier_qualification",
        summary="Qualify ABC as supplier",
        entities=[ExtractedEntity(type="supplier", value="ABC", confidence=0.9)],
        confidence=0.9,
        rationale="Task mentions qualify.",
    )
    assert t.intent == "qualify"


def test_valid_with_null_optional_fields():
    t = TaskUnderstanding(
        intent="process",
        use_case=None,
        summary="Some task",
        entities=[],
        confidence=0.5,
        rationale=None,
    )
    assert t.use_case is None
    assert t.rationale is None


def test_invalid_extra_field_rejected():
    """extra='forbid' should reject unknown fields."""
    with pytest.raises(ValidationError):
        TaskUnderstanding(
            intent="x",
            use_case=None,
            summary="y",
            entities=[],
            confidence=0.5,
            rationale=None,
            unexpected_field="nope",   # type: ignore
        )


def test_invalid_confidence_range():
    with pytest.raises(ValidationError):
        TaskUnderstanding(
            intent="x",
            use_case=None,
            summary="y",
            entities=[],
            confidence=1.5,
            rationale=None,
        )