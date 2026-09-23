"""
Task Understanding schemas.

These define the structured output that the LLM produces when
interpreting an operational task. They are the CONTRACT between
the Task Understanding service and any LLM provider.

DESIGN:
    - Valid use-case values are NOT hardcoded here. They are injected
      into the prompt at runtime from app.use_cases (the registry).
    - Schema is STRICT-MODE compatible (Groq / OpenAI structured output).
        * extra="forbid"               -> additionalProperties: false
        * all fields in `required`     -> nullable where optional
        * no Python defaults           -> no `default` keyword in JSON Schema
    - anyOf (nullable union) and numeric/length constraints (minimum,
      maximum, maxLength) are intentionally kept. They will be verified
      against Groq's live API in Stage 4.4.2 before adjusting.

NOTE:
    Making `use_case`, `rationale`, and `entities` "required" is a
    Groq strict-mode requirement. Null / empty-list are still valid
    values, so downstream code is unaffected.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExtractedEntity(BaseModel):
    """A single entity extracted from the task."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        ...,
        description="Entity type, e.g., 'supplier', 'order_id', 'customer_id'",
    )
    value: str = Field(..., description="The extracted value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence that this entity is correct (0.0-1.0)",
    )


class TaskUnderstanding(BaseModel):
    """
    Structured interpretation of an operational task.

    Produced by the Task Understanding service (which calls the LLM).
    Consumed by downstream stages: Requirement Engine, Retrieval, etc.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "intent": "qualify",
                "use_case": "supplier_qualification",
                "summary": "Qualify ABC Components as a new supplier",
                "entities": [
                    {"type": "supplier", "value": "ABC Components", "confidence": 0.95},
                    {"type": "supplier_id", "value": "S-1042", "confidence": 1.0},
                ],
                "confidence": 0.9,
                "rationale": "Task explicitly mentions supplier qualification and onboarding.",
            }
        },
    )

    intent: str = Field(
        ...,
        description=(
            "High-level intent: 'qualify', 'resolve', 'investigate', "
            "'onboard', 'review', 'verify', etc."
        ),
    )

    use_case: Optional[str] = Field(
        ...,
        max_length=100,
        description=(
            "Best-fit EACIP use-case identifier, or null if none applies. "
            "Valid values are provided at runtime via the system prompt."
        ),
    )

    summary: str = Field(
        ...,
        max_length=500,
        description="One-sentence summary of what the user wants to accomplish",
    )

    entities: list[ExtractedEntity] = Field(
        ...,
        description="Entities extracted from the task text (may be empty)",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this interpretation",
    )

    rationale: Optional[str] = Field(
        ...,
        max_length=500,
        description=(
            "Brief rationale (1-2 sentences) for the chosen intent and use_case. "
            "Not a step-by-step thinking process. Null if not applicable."
        ),
    )