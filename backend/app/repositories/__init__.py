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
from app.repositories.validation_repository import ValidationRepository
from app.repositories.policy_chunk_repository import (
    PolicyChunkRepository,
)
from app.repositories.package_repository import PackageRepository
from app.repositories.review_repository import ReviewRepository  # NAYA IMPORT

__all__ = [
    "TaskRepository",
    "RequirementRepository",
    "RetrievedRecordRepository",
    "SourceRepository",
    "CorrelationRepository",
    "ValidationRepository",
    "PolicyChunkRepository",
    "PackageRepository",
    "ReviewRepository",  # NAYA
]