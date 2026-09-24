"""
Generic entity-based retriever.

Given a requirement + source + task, this retriever:
    1. Fetches records from the source
    2. Filters them by matching against the task's entities
    3. Returns scored candidates

Design notes:
- Deliberately GENERIC — no per-source special-casing.
- Matching is JSONB text based, works for structured + document + comms.
- SQL filtering (for scale) is a future optimization; for the prototype
  the per-source record set is small, so Python filtering is fine.
- The retriever does NOT persist anything. The retrieval SERVICE
  owns persistence and transaction boundaries.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source, SourceRecord
from app.retrieval.types import RetrievedRecordData


class GenericRetriever:
    """
    Entity-matching retriever for source_records.

    Usage:
        r = GenericRetriever(session)
        results = await r.retrieve(
            source=source_obj,
            entity_values=["S-1042", "ABC Components"],
        )
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        *,
        source: Source,
        entity_values: list[str],
    ) -> list[RetrievedRecordData]:
        """
        Retrieve records from `source` matching any of `entity_values`.

        If `entity_values` is empty, returns an empty list — retrieval
        without entities would be blind (we'd return the whole source,
        which is not useful and dilutes the context).
        """
        if not entity_values:
            return []

        records = await self._load_records(source.id)
        source_key = self._source_key(source)

        results: list[RetrievedRecordData] = []
        for rec in records:
            match = self._match(rec, entity_values)
            if match is None:
                continue
            results.append(
                RetrievedRecordData(
                    source_record_id=rec.id,
                    source_key=source_key,
                    record_type=rec.record_type,
                    external_id=rec.external_id,
                    retrieval_method="entity_match",
                    relevance_score=match["score"],
                    match_reason=match["reason"],
                    extra={"matched_entity": match["entity"]},
                )
            )
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _load_records(self, source_id: UUID) -> list[SourceRecord]:
        result = await self.session.execute(
            select(SourceRecord).where(SourceRecord.source_id == source_id)
        )
        return list(result.scalars().all())

    @staticmethod
    def _source_key(source: Source) -> str:
        return (source.source_metadata or {}).get("source_key", "")

    @staticmethod
    def _match(
        record: SourceRecord,
        entity_values: list[str],
    ) -> Optional[dict[str, Any]]:
        """
        Match a record against entity values.

        Priority:
            1. external_id exact (case-insensitive) → score 1.0
            2. JSON data contains value → score 0.8
        Returns None if no match.
        """
        external_id = (record.external_id or "").lower()
        data_blob = _flatten_to_lower_string(record.data or {})

        for raw in entity_values:
            value = (raw or "").strip()
            if not value:
                continue
            v_lower = value.lower()

            if v_lower and v_lower == external_id:
                return {
                    "score": 1.0,
                    "reason": f"external_id matches '{value}'",
                    "entity": value,
                }

            if v_lower and v_lower in data_blob:
                return {
                    "score": 0.8,
                    "reason": f"record data references '{value}'",
                    "entity": value,
                }

        return None


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _flatten_to_lower_string(obj: Any) -> str:
    """
    Serialize a nested JSON object into a single lowercase string.

    Used for simple substring matching. This is intentionally naive:
    the prototype's record sets are small, and the goal is a robust
    'contains this entity' check across heterogeneous schemas.
    """
    parts: list[str] = []

    def _walk(x: Any) -> None:
        if x is None:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                parts.append(str(k))
                _walk(v)
        elif isinstance(x, (list, tuple)):
            for item in x:
                _walk(item)
        else:
            parts.append(str(x))

    _walk(obj)
    return " ".join(parts).lower()