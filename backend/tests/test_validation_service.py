"""
Stage 9 validation service tests.

Covers: gap detection by severity, no-gap when records exist,
inconsistency detection, no-inconsistency on match, comparable-field
whitelist enforcement, idempotency, and transaction rollback.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.task import Task
from app.models.task_requirement import TaskRequirement
from app.repositories import ValidationRepository
from app.services import ValidationService


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def req(requirement_type: str, is_mandatory: bool, priority: int = 1):
    return SimpleNamespace(
        id=uuid4(),
        requirement_type=requirement_type,
        is_mandatory=is_mandatory,
        source_hint="some-source",
        priority=priority,
    )


def retrieved_for(requirement_id):
    return SimpleNamespace(
        requirement_id=requirement_id,
        source_record_id=uuid4(),
        retrieval_metadata={"source_key": "some-source"},
    )


def src_rec(external_id, record_type, data):
    return SimpleNamespace(
        id=uuid4(),
        external_id=external_id,
        record_type=record_type,
        data=data,
    )


def corr(a, b):
    return SimpleNamespace(record_a_id=a.id, record_b_id=b.id)


# ---------------------------------------------------------------------
# 1. Gap detection — mandatory → high severity
# ---------------------------------------------------------------------

def test_detect_gap_mandatory_high_severity():
    r = req("esg_evidence", is_mandatory=True)
    rows = ValidationService._detect_gaps([r], retrieved=[])
    assert len(rows) == 1
    row = rows[0]
    assert row["validation_type"] == "missing_requirement"
    assert row["severity"] == "high"
    assert row["requirement_id"] == r.id
    assert row["details"]["requirement_type"] == "esg_evidence"


# ---------------------------------------------------------------------
# 2. Gap detection — optional → low severity
# ---------------------------------------------------------------------

def test_detect_gap_optional_low_severity():
    r = req("delivery_performance", is_mandatory=False)
    rows = ValidationService._detect_gaps([r], retrieved=[])
    assert len(rows) == 1
    assert rows[0]["severity"] == "low"


# ---------------------------------------------------------------------
# 3. No gap when records exist
# ---------------------------------------------------------------------

def test_no_gap_when_records_exist():
    r = req("financial_info", is_mandatory=True)
    rows = ValidationService._detect_gaps(
        [r], retrieved=[retrieved_for(r.id)]
    )
    assert rows == []


# ---------------------------------------------------------------------
# 4. Inconsistency detected on field conflict
# ---------------------------------------------------------------------

def test_detect_inconsistency_on_conflict():
    sup = src_rec("S-1042", "supplier", {
        "supplier_name": "ABC Components",
        "registered_city": "Pune",
        "country": "India",
    })
    cert = src_rec("DOC-GST-ABC", "certificate", {
        "supplier_name": "ABC Components",
        "registered_city": "Mumbai",
        "country": "India",
    })
    c = corr(sup, cert)
    source_key = {sup.id: "supplier-db", cert.id: "document-repo"}
    rows = ValidationService._detect_inconsistencies(
        [c], {sup.id: sup, cert.id: cert}, source_key
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["validation_type"] == "inconsistency"
    assert row["severity"] == "medium"
    assert row["details"]["conflict_count"] == 1
    assert row["details"]["conflicts"][0]["field"] == "registered_city"


# ---------------------------------------------------------------------
# 5. No inconsistency when values match
# ---------------------------------------------------------------------

def test_no_inconsistency_when_values_match():
    sup = src_rec("S-1042", "supplier", {
        "supplier_name": "ABC Components",
        "registered_city": "Pune",
    })
    cert = src_rec("DOC-GST-ABC", "certificate", {
        "supplier_name": "ABC Components",
        "registered_city": "Pune",
    })
    c = corr(sup, cert)
    source_key = {sup.id: "supplier-db", cert.id: "document-repo"}
    rows = ValidationService._detect_inconsistencies(
        [c], {sup.id: sup, cert.id: cert}, source_key
    )
    assert rows == []


# ---------------------------------------------------------------------
# 6. Only comparable fields compared
# ---------------------------------------------------------------------

def test_only_comparable_fields_used():
    qi1 = src_rec("QI-101", "quality_incident", {"severity": "low"})
    qi2 = src_rec("QI-102", "quality_incident", {"severity": "high"})
    c = corr(qi1, qi2)
    source_key = {qi1.id: "quality-system", qi2.id: "quality-system"}
    rows = ValidationService._detect_inconsistencies(
        [c], {qi1.id: qi1, qi2.id: qi2}, source_key
    )
    assert rows == []


# ---------------------------------------------------------------------
# 7. Idempotency — run twice → same result
# ---------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_service_idempotent(db_session):
    task = Task(
        title="Idempotency test",
        description="Test description",
        use_case="supplier_qualification",
        status="pending",
        task_metadata={},
    )
    db_session.add(task)
    await db_session.flush()

    task_id = task.id

    requirement = TaskRequirement(
        task_id=task_id,
        requirement_type="esg_evidence",
        description="ESG evidence",
        is_mandatory=True,
        source_hint="document-repo",
        priority=1,
        requirement_metadata={},
    )
    db_session.add(requirement)
    await db_session.commit()

    service = ValidationService(db_session)

    s1 = await service.validate_for_task(task_id)
    assert s1.total_gaps == 1
    assert s1.total_inconsistencies == 0

    s2 = await service.validate_for_task(task_id)
    assert s2.total_gaps == 1

    # DB has exactly ONE gap, not two
    repo = ValidationRepository(db_session)
    rows = await repo.get_by_task_id(task_id)
    assert len(rows) == 1

    # Cleanup
    fetched = await db_session.get(Task, task_id)
    if fetched is not None:
        await db_session.delete(fetched)
        await db_session.commit()


# ---------------------------------------------------------------------
# 8. Rollback on insert failure
# ---------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rollback_on_insert_failure(db_session):
    task = Task(
        title="Rollback test",
        description="Test description",
        use_case="supplier_qualification",
        status="pending",
        task_metadata={},
    )
    db_session.add(task)
    await db_session.commit()

    # IMPORTANT: capture the id BEFORE the rollback expires the object.
    # Accessing task.id after rollback triggers a lazy load that requires
    # an async context (MissingGreenlet).
    task_id = task.id

    service = ValidationService(db_session)

    # Force create_many to raise
    service.validation_repo.create_many = AsyncMock(
        side_effect=RuntimeError("forced failure")
    )

    with pytest.raises(RuntimeError):
        await service.validate_for_task(task_id)

    # Task still intact (rollback preserved DB state)
    fetched = await db_session.get(Task, task_id)
    assert fetched is not None

    # No partial validations left
    repo = ValidationRepository(db_session)
    rows = await repo.get_by_task_id(task_id)
    assert rows == []

    # Cleanup
    await db_session.delete(fetched)
    await db_session.commit()