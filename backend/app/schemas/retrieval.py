"""
Retrieval schemas.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetrievedRecordResponse(BaseModel):
    """A single retrieved record attached to a task."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    requirement_id: Optional[UUID] = None
    source_record_id: UUID
    retrieval_method: str
    relevance_score: Optional[float] = None
    is_selected: bool
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedRecordListResponse(BaseModel):
    """List of retrieved records for a task."""

    records: list[RetrievedRecordResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)


class RunRetrievalResponse(BaseModel):
    """Summary after running retrieval for a task."""

    task_id: UUID
    total_retrieved: int
    requirements_processed: int
    requirements_skipped: int
    """Requirements without source_hint or source not found."""
    sources_used: list[str] = Field(default_factory=list)
    run_at: str