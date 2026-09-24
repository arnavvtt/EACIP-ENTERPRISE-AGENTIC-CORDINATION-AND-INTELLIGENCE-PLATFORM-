"""
Anchor resolution.

1. Choose anchor entity via ANCHOR_PREFERENCE[use_case]
   (ordered; first type that matches; confidence is tie-breaker).
2. Resolve anchor record via ANCHOR_RESOLUTION_FIELDS[entity.type].

Exact-match only. No fuzzy / substring matching.
"""

from typing import Iterable, Optional

from app.correlation.rules import (
    ANCHOR_PREFERENCE,
    ANCHOR_RESOLUTION_FIELDS,
)
from app.correlation.types import AnchorResolution, EntityRef


def select_anchor_entity(
    entities: list[EntityRef],
    use_case: str,
) -> Optional[EntityRef]:
    by_type: dict[str, list[EntityRef]] = {}
    for e in entities:
        by_type.setdefault(e.type.lower().strip(), []).append(e)

    preferred = ANCHOR_PREFERENCE.get(use_case, ())
    for ptype in preferred:
        bucket = by_type.get(ptype.lower())
        if bucket:
            return max(bucket, key=lambda e: e.confidence)

    resolvable = [
        e for e in entities
        if e.type.lower().strip() in ANCHOR_RESOLUTION_FIELDS
    ]
    if not resolvable:
        return None
    return max(resolvable, key=lambda e: e.confidence)


def resolve_anchor_record(
    anchor_entity: EntityRef,
    records: Iterable,
) -> Optional[AnchorResolution]:
    fields = ANCHOR_RESOLUTION_FIELDS.get(anchor_entity.type.lower().strip())
    if not fields:
        return None

    target = anchor_entity.value.strip()
    if not target:
        return None

    for rec in records:
        for field_name in fields:
            value = _read_field(rec, field_name)
            if value is None:
                continue
            if str(value).strip() == target:
                return AnchorResolution(
                    record_id=rec.id,
                    record_external_id=rec.external_id,
                    record_type=rec.record_type,
                    matched_field=field_name,
                    matched_value=str(value),
                )
    return None


def _read_field(record, field_name: str):
    if field_name == "external_id":
        return record.external_id
    data = record.data or {}
    return data.get(field_name)