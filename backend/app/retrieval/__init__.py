"""
Retrieval — generic retrieval from source_records and policy_chunks.
"""

from app.retrieval.retriever import GenericRetriever
from app.retrieval.lexical_retriever import LexicalRetriever
from app.retrieval.semantic_retriever import SemanticRetriever
from app.retrieval.rrf_fusion import reciprocal_rank_fusion, RRF_K
from app.retrieval.types import (
    FusedHit,
    LexicalHit,
    RetrievedRecordData,
    SemanticHit,
)

__all__ = [
    "GenericRetriever",
    "LexicalRetriever",
    "SemanticRetriever",
    "reciprocal_rank_fusion",
    "RRF_K",
    "RetrievedRecordData",
    "LexicalHit",
    "SemanticHit",
    "FusedHit",
]