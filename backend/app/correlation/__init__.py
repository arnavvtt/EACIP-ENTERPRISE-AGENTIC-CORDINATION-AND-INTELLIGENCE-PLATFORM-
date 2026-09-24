"""
Correlation — deterministic record-to-record relationships.
"""

from app.correlation.engine import EngineResult, run_correlation_engine
from app.correlation.types import (
    AnchorResolution,
    CorrelationCandidate,
    EntityRef,
)

__all__ = [
    "run_correlation_engine",
    "EngineResult",
    "AnchorResolution",
    "CorrelationCandidate",
    "EntityRef",
]