"""
Source layer models.

- Source: metadata about where data comes from
- SourceRecord: actual raw records stored from sources

These two tables represent EACIP's input layer. All retrieval
and context construction is built on top of these records.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Source(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents an external or simulated data source.

    Examples:
    - "Supplier DB" (structured_db)
    - "Procurement DB" (structured_db)
    - "Policies Repository" (document_store)
    - "Email Archive" (communication)
    - "Compliance API" (api)
    """

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable source name",
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="structured_db | document_store | api | communication",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the source",
    )

    connection_info: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Flexible connection metadata (host, credentials ref, etc.)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether this source is currently active",
    )

    source_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra source-specific metadata",
    )

    # Relationship: one source -> many records
    records: Mapped[list["SourceRecord"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id} name={self.name!r} type={self.source_type!r}>"


class SourceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A raw record from a source.

    Examples:
    - A supplier row: external_id='S-1042', record_type='supplier', data={...}
    - An order row: external_id='PO-4821', record_type='purchase_order', data={...}
    - A policy document: external_id='POL-001', record_type='policy', data={text:...}
    """

    __tablename__ = "source_records"

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source this record belongs to",
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Source system's own identifier (e.g., S-1042, PO-4821)",
    )

    record_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Record type: supplier, purchase_order, certificate, policy, etc.",
    )

    data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="The actual record data (use-case specific schema)",
    )

    record_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Extra metadata: fetch time, ingestion info, etc.",
    )

    # Relationship back to source
    source: Mapped["Source"] = relationship(back_populates="records")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_id",
            name="uq_source_records_source_external_id",
        ),
        Index(
            "ix_source_records_source_type",
            "source_id",
            "record_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SourceRecord id={self.id} "
            f"external_id={self.external_id!r} "
            f"type={self.record_type!r}>"
        )