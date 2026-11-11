"""
Pydantic schemas for Operational Package.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PackageGenerateResponse(BaseModel):
    task_id: UUID
    package_id: UUID
    version: int
    status: str
    generated_at: datetime
    sections_count: int
    summary: str


class PackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    version: int
    status: str
    sections: dict[str, Any]
    summary: Optional[str]
    generated_by: str
    package_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime