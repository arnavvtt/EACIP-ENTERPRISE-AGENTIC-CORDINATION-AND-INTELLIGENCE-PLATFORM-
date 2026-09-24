"""
Retrieval — generic entity-based retrieval from source_records.
"""

from app.retrieval.retriever import GenericRetriever
from app.retrieval.types import RetrievedRecordData

__all__ = [
    "GenericRetriever",
    "RetrievedRecordData",
]