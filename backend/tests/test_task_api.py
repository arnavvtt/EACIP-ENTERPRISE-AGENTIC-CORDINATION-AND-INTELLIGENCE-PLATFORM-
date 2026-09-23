"""
Tests for task API endpoints.

Cleanup strategy:
    Since there is no DELETE /tasks/{id} endpoint, and tests share
    the same PostgreSQL database, we clean up via a direct DB session
    after each test. This keeps the suite idempotent.

Covers:
- POST /tasks (create)
- POST /tasks (validation errors)
- GET /tasks (list + pagination validation)
- GET /tasks/{id} (fetch, not found)
"""

from uuid import UUID, uuid4

import pytest

from app.database import AsyncSessionLocal
from app.repositories import TaskRepository


async def _cleanup_task(task_id: UUID) -> None:
    """Direct DB cleanup after API test (no DELETE endpoint exists)."""
    async with AsyncSessionLocal() as session:
        repo = TaskRepository(session)
        task = await repo.get_by_id(task_id)
        if task is not None:
            await session.delete(task)
            await session.commit()


# =====================================================================
# POST /tasks
# =====================================================================


@pytest.mark.asyncio
async def test_create_task_api(client):
    response = await client.post("/tasks", json={
        "title": "API test",
        "description": "Desc",
        "use_case": "supplier_qualification",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "API test"
    assert data["status"] == "pending"
    assert data["use_case"] == "supplier_qualification"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    await _cleanup_task(UUID(data["id"]))


@pytest.mark.asyncio
async def test_create_task_without_use_case(client):
    response = await client.post("/tasks", json={
        "title": "No use case",
        "description": "Desc",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["use_case"] is None

    await _cleanup_task(UUID(data["id"]))


@pytest.mark.asyncio
async def test_create_task_invalid_empty_title(client):
    response = await client.post("/tasks", json={
        "title": "",
        "description": "Desc",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_long_title(client):
    response = await client.post("/tasks", json={
        "title": "x" * 501,
        "description": "Desc",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_missing_description(client):
    response = await client.post("/tasks", json={
        "title": "Only title",
    })
    assert response.status_code == 422


# =====================================================================
# GET /tasks
# =====================================================================


@pytest.mark.asyncio
async def test_list_tasks_api(client):
    response = await client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    assert isinstance(data["tasks"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_list_tasks_pagination_limit_zero(client):
    """limit must be >= 1."""
    response = await client.get("/tasks", params={"limit": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_pagination_limit_too_high(client):
    """limit must be <= 100."""
    response = await client.get("/tasks", params={"limit": 101})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_pagination_offset_negative(client):
    """offset must be >= 0."""
    response = await client.get("/tasks", params={"offset": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_pagination_valid(client):
    response = await client.get("/tasks", params={"limit": 10, "offset": 0})
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) <= 10


# =====================================================================
# GET /tasks/{id}
# =====================================================================


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    response = await client.get(f"/tasks/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task_api(client):
    # Create first
    create_resp = await client.post("/tasks", json={
        "title": "Get test",
        "description": "Desc",
    })
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    # Then fetch
    get_resp = await client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == task_id
    assert data["title"] == "Get test"

    await _cleanup_task(UUID(task_id))


@pytest.mark.asyncio
async def test_get_task_invalid_uuid(client):
    """Invalid UUID format should return 422."""
    response = await client.get("/tasks/not-a-uuid")
    assert response.status_code == 422