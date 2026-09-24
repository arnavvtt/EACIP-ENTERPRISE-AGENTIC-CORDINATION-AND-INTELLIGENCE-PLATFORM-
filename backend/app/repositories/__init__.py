"""
Repositories — data access layer.
"""

from app.repositories.task_repository import TaskRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.retrieved_record_repository import (
    RetrievedRecordRepository,
)
from app.repositories.source_repository import SourceRepository
from app.repositories.correlation_repository import CorrelationRepository

__all__ = [
    "TaskRepository",
    "RequirementRepository",
    "RetrievedRecordRepository",
    "SourceRepository",
    "CorrelationRepository",
]