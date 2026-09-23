"""
Task Pydantic schemas.

These schemas define the shape of data flowing in and out of the
task API. They handle validation, serialization, and OpenAPI docs
generation automatically via FastAPI.

Design rules:
- TaskCreate: only fields the client is allowed to set.
- TaskResponse: fields the client is allowed to see.
- TaskListResponse: a wrapper for collections (allows future pagination).
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# INPUT SCHEMAS — what clients send TO the API
# =====================================================================


class TaskCreate(BaseModel):
    """
    Schema for creating a new task.

    Only fields a client is allowed to provide.
    System-generated fields (id, status, intent, timestamps) are excluded.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Short human-readable title of the task",
        examples=["Qualify ABC Components as supplier"],
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Raw task description as submitted by the user",
        examples=[
            "Prepare the complete operational context required to "
            "qualify ABC Components as a supplier."
        ],
    )

    use_case: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional use case identifier",
        examples=["supplier_qualification"],
    )


# =====================================================================
# OUTPUT SCHEMAS — what clients receive FROM the API
# =====================================================================


class TaskResponse(BaseModel):
    """
    Schema for a single task in API responses.

    Uses `from_attributes=True` so Pydantic can build this from a
    SQLAlchemy model instance directly.
    """

    id: UUID
    title: str
    description: str
    use_case: Optional[str] = None
    status: str
    intent: Optional[str] = None
    task_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """
    Schema for a list of tasks.

    Wrapped in an object (instead of bare list) to allow future
    additions like pagination without breaking the API contract.
    """

    tasks: list[TaskResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)