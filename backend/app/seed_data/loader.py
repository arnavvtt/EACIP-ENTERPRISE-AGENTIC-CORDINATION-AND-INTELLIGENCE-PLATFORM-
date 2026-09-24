"""
Seed data loader.

Loads simulated enterprise data from JSON files into the
`sources` and `source_records` tables.

Source identity:
    Sources are uniquely identified by `source_metadata["source_key"]`
    (canonical, e.g. "supplier-db"). Display names are human-readable
    and may change; the source_key is stable and is what Stage 5
    source_hints (and Stage 6 retrieval) resolve against.

Usage (from container):
    python -m app.seed_data.loader --use-case supplier_qualification

Behavior:
    Idempotent: existing source_records for the seeded sources are
    deleted before re-insertion. Sources themselves are upserted by
    source_key.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.source import Source, SourceRecord


# ---------------------------------------------------------------------
# Paths + file map
# ---------------------------------------------------------------------

SEED_ROOT = Path(__file__).resolve().parent


# For each use case: list of (json_filename, canonical_source_key)
RECORD_FILES: dict[str, list[tuple[str, str]]] = {
    "supplier_qualification": [
        ("suppliers.json", "supplier-db"),
        ("purchase_orders.json", "procurement-db"),
        ("quality_incidents.json", "quality-system"),
        ("documents.json", "document-repo"),
        ("communications.json", "comms-archive"),
    ],
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------

async def load_use_case(use_case: str) -> None:
    if use_case not in RECORD_FILES:
        raise ValueError(f"Unknown use_case '{use_case}'")

    folder = SEED_ROOT / use_case
    if not folder.exists():
        raise FileNotFoundError(f"Seed folder not found: {folder}")

    async with AsyncSessionLocal() as session:
        source_map = await _upsert_sources(session, folder / "sources.json")
        print(f"[loader] Sources upserted: {len(source_map)}")

        await _delete_existing_records(session, source_map)
        print(f"[loader] Existing records deleted")

        total_inserted = 0
        for filename, source_key in RECORD_FILES[use_case]:
            source = source_map.get(source_key)
            if source is None:
                raise ValueError(
                    f"Source not found for key '{source_key}' "
                    f"(file '{filename}')"
                )
            records = _load_json(folder / filename)
            await _insert_records(session, source, records)
            total_inserted += len(records)
            print(
                f"[loader] Inserted {len(records):>3} records "
                f"from {filename} -> {source_key}"
            )

        await session.commit()
        print(f"[loader] Done. Total records inserted: {total_inserted}")


async def _upsert_sources(
    session: AsyncSession, sources_file: Path
) -> dict[str, Source]:
    """
    Upsert sources by `source_metadata["source_key"]`.

    Returns: {source_key: Source}
    """
    raw = _load_json(sources_file)

    # Load all existing sources once and index by source_key
    result = await session.execute(select(Source))
    existing_by_key: dict[str, Source] = {}
    for s in result.scalars().all():
        key = (s.source_metadata or {}).get("source_key")
        if key:
            existing_by_key[key] = s

    source_map: dict[str, Source] = {}
    for item in raw:
        metadata = item.get("source_metadata", {}) or {}
        key = metadata.get("source_key")
        if not key:
            raise ValueError(
                f"Source '{item.get('name')}' missing source_metadata.source_key"
            )

        existing = existing_by_key.get(key)
        if existing is not None:
            # Refresh display fields (name/description may evolve)
            existing.name = item["name"]
            existing.source_type = item["source_type"]
            existing.description = item.get("description")
            existing.connection_info = item.get("connection_info", {})
            existing.is_active = item.get("is_active", True)
            existing.source_metadata = metadata
            source_map[key] = existing
            continue

        src = Source(
            name=item["name"],
            source_type=item["source_type"],
            description=item.get("description"),
            connection_info=item.get("connection_info", {}),
            is_active=item.get("is_active", True),
            source_metadata=metadata,
        )
        session.add(src)
        await session.flush()
        source_map[key] = src

    return source_map


async def _delete_existing_records(
    session: AsyncSession, source_map: dict[str, Source]
) -> None:
    """Delete all source_records for these sources (idempotent seeding)."""
    source_ids = [s.id for s in source_map.values()]
    if not source_ids:
        return
    await session.execute(
        delete(SourceRecord).where(SourceRecord.source_id.in_(source_ids))
    )


async def _insert_records(
    session: AsyncSession, source: Source, records: list[dict]
) -> None:
    for rec in records:
        session.add(
            SourceRecord(
                source_id=source.id,
                external_id=rec["external_id"],
                record_type=rec["record_type"],
                data=rec.get("data", {}),
                record_metadata=rec.get("record_metadata", {}),
            )
        )
    await session.flush()


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-case", required=True)
    args = parser.parse_args()
    asyncio.run(load_use_case(args.use_case))


if __name__ == "__main__":
    main()