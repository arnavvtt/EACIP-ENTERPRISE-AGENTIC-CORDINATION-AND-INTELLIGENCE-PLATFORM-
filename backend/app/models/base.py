"""
Common mixins and base classes for all EACIP models.

This module provides reusable mixins that are applied across all
database models to ensure consistency (timestamps, etc.).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Adds created_at and updated_at timestamps to any model.

    Why every table needs this:
    - Audit trail: When was this record created/modified?
    - Research: Evaluation needs timestamps for time-based analysis
    - Debugging: Helps trace issues
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """
    Adds a UUID primary key to any model.

    Why UUID instead of auto-increment integer:
    - Distributed-friendly (no collision across services)
    - Doesn't leak record count (security)
    - Can be generated client-side if needed
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )