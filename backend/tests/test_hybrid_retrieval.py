"""
Tests for RRF fusion.

Pure-function tests — no DB, no API.
"""

from uuid import uuid4

from app.retrieval.rrf_fusion import (
    RRF_K,
    reciprocal_rank_fusion,
)
from app.retrieval.types import LexicalHit, SemanticHit


def _lex(chunk_id, chunk_index=0, rank=0.5):
    return LexicalHit(
        chunk_id=chunk_id,
        source_record_id=uuid4(),
        chunk_index=chunk_index,
        chunk_text=f"chunk {chunk_index}",
        rank=rank,
    )


def _sem(chunk_id, chunk_index=0, sim=0.5):
    return SemanticHit(
        chunk_id=chunk_id,
        source_record_id=uuid4(),
        chunk_index=chunk_index,
        chunk_text=f"chunk {chunk_index}",
        similarity=sim,
    )


def test_empty_inputs():
    fused = reciprocal_rank_fusion([], [])
    assert fused == []


def test_only_lexical():
    id_a = uuid4()
    id_b = uuid4()
    fused = reciprocal_rank_fusion(
        [_lex(id_a, 0), _lex(id_b, 1)],
        [],
    )
    assert len(fused) == 2
    # rank 1 (id_a) should beat rank 2 (id_b)
    assert fused[0].chunk_id == id_a
    assert fused[0].lexical_rank == 1
    assert fused[0].semantic_rank is None


def test_only_semantic():
    id_a = uuid4()
    fused = reciprocal_rank_fusion([], [_sem(id_a, 0)])
    assert len(fused) == 1
    assert fused[0].semantic_rank == 1
    assert fused[0].lexical_rank is None


def test_document_in_both_lists_boosted():
    id_a = uuid4()
    id_b = uuid4()
    # id_a in both lists at rank 1
    # id_b only in lexical at rank 2
    fused = reciprocal_rank_fusion(
        [_lex(id_a, 0), _lex(id_b, 1)],
        [_sem(id_a, 0)],
    )
    assert len(fused) == 2
    # id_a wins because it's in both
    assert fused[0].chunk_id == id_a
    assert fused[0].lexical_rank == 1
    assert fused[0].semantic_rank == 1
    # id_b second
    assert fused[1].chunk_id == id_b


def test_rrf_score_correct_for_single_list():
    id_a = uuid4()
    fused = reciprocal_rank_fusion([_lex(id_a, 0)], [])
    # rank 1 → 1 / (60 + 1)
    expected = 1.0 / (RRF_K + 1)
    assert abs(fused[0].rrf_score - expected) < 1e-9


def test_rrf_score_correct_for_both_lists():
    id_a = uuid4()
    fused = reciprocal_rank_fusion(
        [_lex(id_a, 0)],
        [_sem(id_a, 0)],
    )
    # rank 1 in both → 2 * 1 / (60 + 1)
    expected = 2.0 / (RRF_K + 1)
    assert abs(fused[0].rrf_score - expected) < 1e-9


def test_sorted_descending_by_score():
    id_a = uuid4()
    id_b = uuid4()
    id_c = uuid4()
    fused = reciprocal_rank_fusion(
        [_lex(id_a, 0), _lex(id_b, 1), _lex(id_c, 2)],
        [_sem(id_a, 0)],
    )
    scores = [h.rrf_score for h in fused]
    assert scores == sorted(scores, reverse=True)