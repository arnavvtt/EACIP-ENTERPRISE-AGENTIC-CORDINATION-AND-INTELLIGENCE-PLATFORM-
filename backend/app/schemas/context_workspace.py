"""
Context Workspace schema.
"""

from pydantic import BaseModel, Field

from app.schemas.correlation import CorrelationResponse
from app.schemas.requirement import TaskRequirementResponse
from app.schemas.retrieval import RetrievedRecordResponse
from app.schemas.task import TaskResponse
from app.schemas.validation import ValidationResponse


class ContextWorkspaceResponse(BaseModel):
    """Aggregated context for a task — one call, one page."""

    task: TaskResponse
    requirements: list[TaskRequirementResponse]
    retrieved_records: list[RetrievedRecordResponse]
    correlations: list[CorrelationResponse] = Field(default_factory=list)
    validations: list[ValidationResponse] = Field(default_factory=list)