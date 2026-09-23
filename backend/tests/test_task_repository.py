"""
Tests for TaskRepository.

Verifies DB-level operations in isolation from API/service layers.
Each test cleans up its own data so the suite stays idempotent.
"""

from uuid import uuid4

import pytest
import pytest_asyncio

from app.repositories import TaskRepository


@pytest_asyncio.fixture
async def repo(db_session):
    return TaskRepository(db_session)


@pytest.mark.asyncio
async def test_create_task(repo, db_session):
    task = await repo.create(
        title="Test repo",
        description="Desc",
        use_case="supplier_qualification",
    )
    assert task.id is not None
    assert task.status == "pending"
    assert task.title == "Test repo"
    assert task.use_case == "supplier_qualification"

    await db_session.commit()
    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_task_without_use_case(repo, db_session):
    task = await repo.create(title="No use case", description="Desc")
    assert task.use_case is None

    await db_session.commit()
    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_by_id(repo, db_session):
    task = await repo.create(title="T", description="D")
    await db_session.commit()

    fetched = await repo.get_by_id(task.id)
    assert fetched is not None
    assert fetched.id == task.id
    assert fetched.title == "T"

    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_by_id_not_found(repo):
    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_all(repo, db_session):
    task = await repo.create(title="List test", description="D")
    await db_session.commit()

    tasks = await repo.list_all()
    assert len(tasks) >= 1
    assert any(t.id == task.id for t in tasks)

    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_all_newest_first(repo, db_session):
    task1 = await repo.create(title="First", description="D")
    await db_session.commit()
    task2 = await repo.create(title="Second", description="D")
    await db_session.commit()

    tasks = await repo.list_all()
    # Second should appear before First (newest first)
    ids = [t.id for t in tasks]
    assert ids.index(task2.id) < ids.index(task1.id)

    await db_session.delete(task1)
    await db_session.delete(task2)
    await db_session.commit()


@pytest.mark.asyncio
async def test_count(repo, db_session):
    before = await repo.count()
    task = await repo.create(title="Count test", description="D")
    await db_session.commit()

    after = await repo.count()
    assert after == before + 1

    await db_session.delete(task)
    await db_session.commit()