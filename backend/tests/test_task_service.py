"""
Tests for TaskService.

Verifies business logic and transaction handling above the repository
layer. Each test cleans up its own data.
"""

import pytest
import pytest_asyncio

from app.schemas.task import TaskCreate
from app.services import TaskService


@pytest_asyncio.fixture
async def service(db_session):
    return TaskService(db_session)


@pytest.mark.asyncio
async def test_create_task(service, db_session):
    task = await service.create_task(TaskCreate(
        title="Service test",
        description="Desc",
        use_case="supplier_qualification",
    ))
    assert task.id is not None
    assert task.status == "pending"
    assert task.title == "Service test"

    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_task_without_use_case(service, db_session):
    task = await service.create_task(TaskCreate(
        title="No use case",
        description="Desc",
    ))
    assert task.use_case is None

    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_task(service, db_session):
    task = await service.create_task(TaskCreate(
        title="Get test",
        description="Desc",
    ))

    fetched = await service.get_task(task.id)
    assert fetched is not None
    assert fetched.id == task.id

    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_task_not_found(service):
    from uuid import uuid4
    result = await service.get_task(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_tasks(service, db_session):
    task = await service.create_task(TaskCreate(
        title="List test",
        description="Desc",
    ))

    tasks, total = await service.list_tasks()
    assert total >= 1
    assert any(t.id == task.id for t in tasks)

    await db_session.delete(task)
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_tasks_pagination(service, db_session):
    t1 = await service.create_task(TaskCreate(title="P1", description="D"))
    t2 = await service.create_task(TaskCreate(title="P2", description="D"))

    tasks, total = await service.list_tasks(limit=1, offset=0)
    assert len(tasks) == 1
    assert total >= 2

    await db_session.delete(t1)
    await db_session.delete(t2)
    await db_session.commit()