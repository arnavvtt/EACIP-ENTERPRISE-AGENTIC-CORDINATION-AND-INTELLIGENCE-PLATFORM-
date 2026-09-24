"""
Correlation engine.

Consumes a task's retrieved records and produces correlation
candidates for storage.

Secondary pairs (non-anchor): matches whose value equals the anchor's
identity value (matched_value or external_id) are EXCLUDED. This
prevents spurious "secondary" correlations between records that merely
share the anchor's identity.
"""

from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from app.correlation.anchor import resolve_anchor_record, select_anchor_entity
from app.correlation.rules import (
    CONFIDENCE,
    CORRELATABLE_FIELDS,
    resolve_relationship_type,
)
from app.correlation.types import (
    AnchorResolution,
    CorrelationCandidate,
    EntityRef,
)


@dataclass
class EngineResult:
    anchor: Optional[AnchorResolution]
    correlations: list[CorrelationCandidate]


def run_correlation_engine(
    *,
    use_case: str,
    entities: list[EntityRef],
    records: list,
) -> EngineResult:
    anchor_entity = select_anchor_entity(entities, use_case)
    if anchor_entity is None:
        return EngineResult(anchor=None, correlations=[])

    anchor = resolve_anchor_record(anchor_entity, records)
    if anchor is None:
        return EngineResult(anchor=None, correlations=[])

    anchor_record = next((r for r in records if r.id == anchor.record_id), None)
    if anchor_record is None:
        return EngineResult(anchor=None, correlations=[])

    candidates: list[CorrelationCandidate] = []

    # Anchor -> all
    for other in records:
        if other.id == anchor_record.id:
            continue
        c = _try_pair(anchor_record, other, anchor=anchor, is_anchor_pair=True)
        if c is not None:
            candidates.append(c)

    # Secondary (non-anchor pairs) — anchor identity values excluded
    non_anchor = [r for r in records if r.id != anchor_record.id]
    for i, r1 in enumerate(non_anchor):
        for r2 in non_anchor[i + 1:]:
            c = _try_pair(r1, r2, anchor=anchor, is_anchor_pair=False)
            if c is not None:
                candidates.append(c)

    # Dedup by canonical pair — keep strongest confidence
    best: dict[tuple[UUID, UUID], CorrelationCandidate] = {}
    for c in candidates:
        key = (c.record_a_id, c.record_b_id)
        if key not in best or c.confidence > best[key].confidence:
            best[key] = c

    return EngineResult(anchor=anchor, correlations=list(best.values()))


def _try_pair(
    rec_a,
    rec_b,
    *,
    anchor: AnchorResolution,
    is_anchor_pair: bool,
) -> Optional[CorrelationCandidate]:
    a_fields = CORRELATABLE_FIELDS.get(rec_a.record_type, ())
    b_fields = CORRELATABLE_FIELDS.get(rec_b.record_type, ())
    if not a_fields or not b_fields:
        return None

    a_values = _approved_values(rec_a, a_fields)
    b_values = _approved_values(rec_b, b_fields)

    matches: list[dict[str, Any]] = []
    for a_field, a_val in a_values.items():
        if a_val is None:
            continue
        target = str(a_val).strip()
        if not target:
            continue
        for b_field, b_val in b_values.items():
            if b_val is None:
                continue
            if str(b_val).strip() == target:
                matches.append({
                    "a_field": a_field,
                    "b_field": b_field,
                    "value": target,
                })

    if not matches:
        return None

    # Secondary pairs: exclude matches whose value IS the anchor's identity.
    # Otherwise any two records sharing the anchor's ID would "correlate".
    if not is_anchor_pair:
        excluded = _anchor_identity_values(anchor)
        matches = [m for m in matches if m["value"] not in excluded]
        if not matches:
            return None

    basis = _determine_basis(rec_a, rec_b, matches, anchor, is_anchor_pair)
    confidence = CONFIDENCE[basis]

    a_id, b_id = _canonical_order(rec_a.id, rec_b.id)
    if a_id == b_id:
        return None

    matched_fields = sorted(
        {m["a_field"] for m in matches} | {m["b_field"] for m in matches}
    )
    primary = matches[0]
    all_matches = [
        {"field": m["a_field"], "value": m["value"]} for m in matches
    ]

    relationship_type = resolve_relationship_type(
        rec_a.record_type, rec_b.record_type
    )

    return CorrelationCandidate(
        record_a_id=a_id,
        record_b_id=b_id,
        relationship_type=relationship_type,
        basis=basis,
        confidence=confidence,
        metadata={
            "anchor_record_id": str(anchor.record_id),
            "anchor_external_id": anchor.record_external_id,
            "anchor_matched_field": anchor.matched_field,
            "anchor_matched_value": anchor.matched_value,
            "matched_value": primary["value"],
            "matched_fields": matched_fields,
            "all_matched_values": all_matches,
            "record_a_external_id": (
                rec_a.external_id if a_id == rec_a.id else rec_b.external_id
            ),
            "record_b_external_id": (
                rec_b.external_id if b_id == rec_b.id else rec_a.external_id
            ),
            "pair_kind": "anchor" if is_anchor_pair else "secondary",
        },
    )


def _anchor_identity_values(anchor: AnchorResolution) -> set[str]:
    """Values that uniquely identify the anchor record."""
    values: set[str] = set()
    if anchor.matched_value:
        values.add(anchor.matched_value.strip())
    if anchor.record_external_id:
        values.add(anchor.record_external_id.strip())
    return values


def _approved_values(record, fields: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    data = record.data or {}
    for f in fields:
        if f == "external_id":
            out[f] = record.external_id
        else:
            out[f] = data.get(f)
    return out


def _determine_basis(
    rec_a,
    rec_b,
    matches: list[dict[str, Any]],
    anchor: AnchorResolution,
    is_anchor_pair: bool,
) -> str:
    if is_anchor_pair:
        for m in matches:
            if m["value"] == (anchor.record_external_id or "").strip():
                return "exact_id"
    return "business_key"


def _canonical_order(id1: UUID, id2: UUID) -> tuple[UUID, UUID]:
    return (id1, id2) if str(id1) < str(id2) else (id2, id1)