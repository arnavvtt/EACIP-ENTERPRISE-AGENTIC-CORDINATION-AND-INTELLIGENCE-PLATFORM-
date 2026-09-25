"""
Reciprocal Rank Fusion (RRF).

Combines multiple ranked lists into a single ranked list using the
RRF formula:

    RRF_score(doc) = Σ  1 / (k + rank_i(doc))
                     i

where:
    k = 60 (standard constant, from Cormack et al. 2009)
    rank_i(doc) = 1-based rank of doc in list i

Design:
- Pure function, no I/O.
- Works on rank, not raw scores — so different score ranges
  (ts_rank_cd vs cosine similarity) are handled naturally.
- Documents appearing in multiple lists get boosted (sum of contributions).
- Documents appearing in only one list still get a score.

This is the industry-standard fusion method used by Elasticsearch,
Vespa, Weaviate, and others.
"""

from app.retrieval.types import (
    FusedHit,
    LexicalHit,
    SemanticHit,
)


# Standard RRF constant from the original paper.
RRF_K = 60


def reciprocal_rank_fusion(
    lexical_hits: list[LexicalHit],
    semantic_hits: list[SemanticHit],
    k: int = RRF_K,
) -> list[FusedHit]:
    """
    Fuse two ranked lists into one using RRF.

    Args:
        lexical_hits: List of LexicalHit sorted by rank (best first).
        semantic_hits: List of SemanticHit sorted by similarity (best first).
        k: RRF constant (default 60).

    Returns:
        FusedHit list sorted by rrf_score descending.
    """
    # Accumulate: chunk_id → {score, chunk info, lexical_rank, semantic_rank}
    scores: dict[str, float] = {}
    info: dict[str, dict] = {}

    # Lexical pass
    for rank, hit in enumerate(lexical_hits, start=1):
        cid = str(hit.chunk_id)
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        info[cid] = {
            "chunk_id": hit.chunk_id,
            "source_record_id": hit.source_record_id,
            "chunk_index": hit.chunk_index,
            "chunk_text": hit.chunk_text,
            "lexical_rank": rank,
            "semantic_rank": None,
        }

    # Semantic pass
    for rank, hit in enumerate(semantic_hits, start=1):
        cid = str(hit.chunk_id)
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        if cid in info:
            info[cid]["semantic_rank"] = rank
        else:
            info[cid] = {
                "chunk_id": hit.chunk_id,
                "source_record_id": hit.source_record_id,
                "chunk_index": hit.chunk_index,
                "chunk_text": hit.chunk_text,
                "lexical_rank": None,
                "semantic_rank": rank,
            }

    # Build result sorted by rrf_score
    fused: list[FusedHit] = []
    for cid, score in scores.items():
        meta = info[cid]
        fused.append(
            FusedHit(
                chunk_id=meta["chunk_id"],
                source_record_id=meta["source_record_id"],
                chunk_index=meta["chunk_index"],
                chunk_text=meta["chunk_text"],
                rrf_score=score,
                lexical_rank=meta["lexical_rank"],
                semantic_rank=meta["semantic_rank"],
            )
        )

    fused.sort(key=lambda h: h.rrf_score, reverse=True)
    return fused