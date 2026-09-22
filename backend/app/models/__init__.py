"""
EACIP database models.

All models must be imported here so that SQLAlchemy's metadata
knows about them. Alembic uses this metadata to autogenerate
migrations.
"""

from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.task import Task
from app.models.source import Source, SourceRecord
from app.models.task_requirement import TaskRequirement
from app.models.retrieved_record import RetrievedRecord
from app.models.correlation import Correlation
from app.models.validation import Validation
from app.models.operational_package import OperationalPackage
from app.models.human_review import HumanReview
from app.models.workflow import Workflow, WorkflowStep
from app.models.assignment import Assignment
from app.models.information_request import InformationRequest
from app.models.audit_log import AuditLog

__all__ = [
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "Task",
    "Source",
    "SourceRecord",
    "TaskRequirement",
    "RetrievedRecord",
    "Correlation",
    "Validation",
    "OperationalPackage",
    "HumanReview",
    "Workflow",
    "WorkflowStep",
    "Assignment",
    "InformationRequest",
    "AuditLog",
]
