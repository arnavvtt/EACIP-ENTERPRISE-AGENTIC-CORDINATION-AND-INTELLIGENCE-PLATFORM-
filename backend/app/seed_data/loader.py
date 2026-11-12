"""
Seed data loader.

Loads simulated enterprise data from JSON files into the
`sources` and `source_records` tables.
Idempotent: Uses an upsert pattern (skip existing, insert new) 
so multiple scopes can share sources (like document-repo) safely.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.source import Source, SourceRecord

SEED_ROOT = Path(__file__).resolve().parent

# NAYA: Added employee_onboarding and purchase_delay
RECORD_FILES: dict[str, list[tuple[str, str]]] = {
    "supplier_qualification": [
        ("suppliers.json", "supplier-db"),
        ("purchase_orders.json", "procurement-db"),
        ("quality_incidents.json", "quality-system"),
        ("documents.json", "document-repo"),
        ("communications.json", "comms-archive"),
    ],
    "employee_onboarding": [
        ("employees.json", "hr-db"),
        ("documents.json", "document-repo"),
        ("it_requests.json", "it-system"),
    ],
    "purchase_delay": [
        ("purchase_orders.json", "procurement-db"),
    ]
}

def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

async def load_use_case(use_case: str) -> None:
    if use_case not in RECORD_FILES:
        raise ValueError(f"Unknown use_case '{use_case}'")

    folder = SEED_ROOT / use_case
    if not folder.exists():
        raise FileNotFoundError(f"Seed folder not found: {folder}")

    async with AsyncSessionLocal() as session:
        source_map = await _upsert_sources(session, folder / "sources.json")
        print(f"[loader] Sources upserted: {len(source_map)}")

        # REMOVED: _delete_existing_records (Ye data wipe kar raha tha)

        total_inserted = 0
        for filename, source_key in RECORD_FILES[use_case]:
            file_path = folder / filename
            if not file_path.exists():
                print(f"[loader] Skipping missing file: {filename}")
                continue

            source = source_map.get(source_key)
            if source is None:
                raise ValueError(f"Source not found for key '{source_key}'")
                
            records = _load_json(file_path)
            inserted = await _insert_records(session, source, records)
            total_inserted += inserted
            print(f"[loader] Processed {len(records):>3} records from {filename} -> {source_key} (Added {inserted})")

        await session.commit()
        print(f"[loader] Done. Total NEW records inserted: {total_inserted}")

async def _upsert_sources(session: AsyncSession, sources_file: Path) -> dict[str, Source]:
    raw = _load_json(sources_file)
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
            raise ValueError(f"Source '{item.get('name')}' missing source_key")

        existing = existing_by_key.get(key)
        if existing is not None:
            existing.name = item["name"]
            existing.source_type = item["source_type"]
            existing.source_metadata = metadata
            source_map[key] = existing
            continue

        src = Source(
            name=item["name"],
            source_type=item["source_type"],
            source_metadata=metadata,
        )
        session.add(src)
        await session.flush()
        source_map[key] = src

    return source_map

async def _insert_records(session: AsyncSession, source: Source, records: list[dict]) -> int:
    """Upserts records (checks if external_id exists)."""
    inserted_count = 0
    
    # Fetch existing records for this source
    stmt = select(SourceRecord).where(SourceRecord.source_id == source.id)
    existing_records = (await session.execute(stmt)).scalars().all()
    existing_map = {r.external_id: r for r in existing_records}

    for rec in records:
        if rec["external_id"] in existing_map:
            # Update existing
            existing = existing_map[rec["external_id"]]
            existing.record_type = rec["record_type"]
            existing.data = rec.get("data", {})
            existing.record_metadata = rec.get("record_metadata", {})
        else:
            # Insert new
            session.add(
                SourceRecord(
                    source_id=source.id,
                    external_id=rec["external_id"],
                    record_type=rec["record_type"],
                    data=rec.get("data", {}),
                    record_metadata=rec.get("record_metadata", {}),
                )
            )
            inserted_count += 1
            
    await session.flush()
    return inserted_count

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-case", required=True)
    args = parser.parse_args()
    asyncio.run(load_use_case(args.use_case))

if __name__ == "__main__":
    main()