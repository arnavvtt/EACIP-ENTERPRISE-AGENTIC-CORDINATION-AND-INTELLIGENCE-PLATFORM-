"""
Retrieval types.

Provider-agnostic shapes for retrieval results. Used across
retrievers and the retrieval service.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID


@dataclass
class RetrievedRecordData:
    """
    A single retrieved record candidate.

    NOTE: This is NOT the DB row. The service converts these into
    `retrieved_records` rows after aggregation/deduplication.
    """

    source_record_id: UUID
    source_key: str
    """Canonical source_key (e.g., 'supplier-db')."""

    record_type: str
    """Record type from source_records (e.g., 'supplier', 'purchase_order')."""

    external_id: str
    """Human-facing id from the source (e.g., 'S-1042', 'PO-4821')."""

    retrieval_method: str
    """'entity_match' for now. Future: 'sql_query', 'vector_search'."""

    relevance_score: Optional[float] = None
    """0.0-1.0 (heuristic). Higher = more confident."""

    match_reason: str = ""
    """Human-readable explanation of why this record matched."""

    extra: dict[str, Any] = field(default_factory=dict)
    """Retriever-specific metadata (matched entity, etc.)."""