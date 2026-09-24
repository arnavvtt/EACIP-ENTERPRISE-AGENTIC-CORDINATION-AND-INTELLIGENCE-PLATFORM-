"""
Requirement schemas.

Two distinct schemas:

1. RequirementCandidate
   - Produced by the LLM (candidate suggestions)
   - NOT authoritative
   - Must be validated/merged before persistence

2. TaskRequirementResponse
   - Produced by the API for reading persisted requirements
   - Maps to the `task_requirements` DB table

The registry (RegistryRequirement) is intentionally NOT a Pydantic
schema — it lives as a frozen dataclass in `requirement_registry.py`.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# LLM-side: candidate (transient, pre-validation)
# =====================================================================

class RequirementCandidate(BaseModel):
    """
    A single LLM-suggested requirement (pre-validation).

    Strict-mode compatible (Groq / OpenAI structured outputs):
    - extra="forbid"
    - all fields in `required` (nullable where optional)
    - no `default` keywords
    """

    model_config = ConfigDict(extra="forbid")

    requirement_type: str = Field(
        ...,
        max_length=100,
        description=(
            "Must be a valid requirement_type from the provided taxonomy. "
            "Validator rejects unknown types."
        ),
    )

    description: str = Field(
        ...,
        max_length=500,
        description="Human-readable description of why this requirement applies",
    )

    is_mandatory: bool = Field(
        ...,
        description=(
            "LLM's opinion on whether this requirement is mandatory. "
            "Note: LLM-only suggestions are always downgraded to "
            "is_mandatory=False during merge."
        ),
    )

    rationale: str = Field(
        ...,
        max_length=500,
        description="Brief rationale (1-2 sentences) for the suggestion",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence that this suggestion is relevant (0.0-1.0)",
    )


# =====================================================================
# API-side: response for persisted requirements
# =====================================================================

class TaskRequirementResponse(BaseModel):
    """
    A persisted requirement attached to a task.

    Mirrors the `task_requirements` DB table. `requirement_metadata`
    carries provenance (registry vs LLM-candidate, validation status,
    rationale, etc.).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    requirement_type: str
    description: str
    is_mandatory: bool
    source_hint: Optional[str] = None
    priority: int
    requirement_metadata: dict[str, Any] = Field(default_factory=dict)


class TaskRequirementListResponse(BaseModel):
    """List of persisted requirements for a task."""

    requirements: list[TaskRequirementResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    # =====================================================================
# LLM-side wrapper (Groq strict mode needs object at root, not array)
# =====================================================================

class RequirementCandidatesOutput(BaseModel):
    """
    Wrapper for LLM structured output.

    Strict-mode providers (Groq/OpenAI) require an object at the root
    of the JSON schema — bare arrays are not supported. So the LLM
    returns {candidates: [...]}, not just [...].
    """

    model_config = ConfigDict(extra="forbid")

    candidates: list[RequirementCandidate] = Field(
        ...,
        max_length=5,
        description=(
            "Task-specific requirement suggestions. Max 5. "
            "Empty list is valid if nothing to add beyond the baseline."
        ),
    )
    # =====================================================================
# API wrapper for identify-requirements endpoint
# =====================================================================

class IdentifyRequirementsResponse(BaseModel):
    """Response after running requirement identification."""

    task_id: UUID
    total_requirements: int
    identified_at: str = Field(
        ...,
        description="ISO timestamp of identification completion",
    )