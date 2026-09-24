"""
Correlation types.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class EntityRef:
    type: str
    value: str
    confidence: float


@dataclass
class AnchorResolution:
    record_id: UUID
    record_external_id: str
    record_type: str
    matched_field: str
    matched_value: str


@dataclass
class CorrelationCandidate:
    record_a_id: UUID
    record_b_id: UUID
    relationship_type: str
    basis: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)
    