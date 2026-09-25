"""
Validation schemas.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    requirement_id: Optional[UUID] = None
    validation_type: str
    severity: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)
    status: str


class ValidationListResponse(BaseModel):
    validations: list[ValidationResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)


class RunValidationResponse(BaseModel):
    task_id: UUID
    total_gaps: int
    total_inconsistencies: int
    by_severity: dict[str, int] = Field(default_factory=dict)
    run_at: str