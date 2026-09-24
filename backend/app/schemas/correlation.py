"""
Correlation schemas.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CorrelationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    record_a_id: UUID
    record_b_id: UUID
    relationship_type: str
    basis: str
    confidence: float
    is_verified: bool
    correlation_metadata: dict[str, Any] = Field(default_factory=dict)


class CorrelationListResponse(BaseModel):
    correlations: list[CorrelationResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)


class RunCorrelationResponse(BaseModel):
    task_id: UUID
    total_correlations: int
    anchor_external_id: str | None = None
    basis_breakdown: dict[str, int] = Field(default_factory=dict)
    run_at: str