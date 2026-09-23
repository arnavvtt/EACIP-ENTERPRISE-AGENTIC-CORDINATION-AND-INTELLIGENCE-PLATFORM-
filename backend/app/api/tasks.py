"""
Task API routes.

Endpoints:
- POST   /tasks              Create a new task
- GET    /tasks              List tasks (paginated)
- GET    /tasks/{task_id}    Get a single task
- POST   /tasks/{task_id}/understand
                             Run task understanding on the task
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
)
from app.services import (
    TaskNotFoundError,
    TaskService,
    TaskUnderstandingError,
    TaskUnderstandingService,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ---------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------

def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return TaskService(db)


def get_understanding_service(
    db: AsyncSession = Depends(get_db),
) -> TaskUnderstandingService:
    return TaskUnderstandingService(db)


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.create_task(payload)
    return TaskResponse.model_validate(task)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks",
)
async def list_tasks(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    tasks, total = await service.list_tasks(limit=limit, offset=offset)
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task",
)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return TaskResponse.model_validate(task)


@router.post(
    "/{task_id}/understand",
    response_model=TaskResponse,
    summary="Run task understanding on a task",
)
async def understand_task(
    task_id: UUID,
    service: TaskUnderstandingService = Depends(get_understanding_service),
) -> TaskResponse:
    """
    Analyze the task using the LLM and persist the structured understanding
    (intent, use_case, entities, confidence, rationale).
    """
    try:
        task = await service.understand_task(task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    except TaskUnderstandingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Task understanding failed: {e}",
        )
    return TaskResponse.model_validate(task)