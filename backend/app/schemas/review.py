"""
Pydantic schemas for Human Review.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    decision: str = Field(..., description="approved or rejected")
    comments: Optional[str] = Field(None, description="Optional feedback")


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    package_id: UUID
    decision: str
    comments: Optional[str]
    created_at: datetime