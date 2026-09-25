"""
Task API routes.

Endpoints:
- POST   /tasks                                    Create a new task
- GET    /tasks                                    List tasks
- GET    /tasks/{task_id}                          Get a single task
- POST   /tasks/{task_id}/understand               Run task understanding
- POST   /tasks/{task_id}/identify-requirements    Identify requirements
- GET    /tasks/{task_id}/requirements             Fetch requirements
- POST   /tasks/{task_id}/retrieve                 Run retrieval
- GET    /tasks/{task_id}/retrieved-records        Fetch retrieved records
- POST   /tasks/{task_id}/correlate                Run correlation
- GET    /tasks/{task_id}/correlations             Fetch correlations
- POST   /tasks/{task_id}/validate                 Run validation
- GET    /tasks/{task_id}/validations              Fetch validations
- GET    /tasks/{task_id}/context                  Aggregated context workspace
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import (
    CorrelationRepository,
    RequirementRepository,
    RetrievedRecordRepository,
    ValidationRepository,
)
from app.schemas.context_workspace import ContextWorkspaceResponse
from app.schemas.correlation import (
    CorrelationListResponse,
    CorrelationResponse,
    RunCorrelationResponse,
)
from app.schemas.requirement import (
    IdentifyRequirementsResponse,
    TaskRequirementListResponse,
    TaskRequirementResponse,
)
from app.schemas.retrieval import (
    RetrievedRecordListResponse,
    RetrievedRecordResponse,
    RunRetrievalResponse,
)
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
)
from app.schemas.validation import (
    RunValidationResponse,
    ValidationListResponse,
    ValidationResponse,
)
from app.services import (
    CorrelationError,
    CorrelationService,
    RequirementError,
    RequirementService,
    RetrievalError,
    RetrievalService,
    TaskNotFoundError,
    TaskService,
    TaskUnderstandingError,
    TaskUnderstandingService,
    ValidationError,
    ValidationService,
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


def get_requirement_service(
    db: AsyncSession = Depends(get_db),
) -> RequirementService:
    return RequirementService(db)


def get_requirement_repo(
    db: AsyncSession = Depends(get_db),
) -> RequirementRepository:
    return RequirementRepository(db)


def get_retrieval_service(
    db: AsyncSession = Depends(get_db),
) -> RetrievalService:
    return RetrievalService(db)


def get_retrieved_repo(
    db: AsyncSession = Depends(get_db),
) -> RetrievedRecordRepository:
    return RetrievedRecordRepository(db)


def get_correlation_service(
    db: AsyncSession = Depends(get_db),
) -> CorrelationService:
    return CorrelationService(db)


def get_correlation_repo(
    db: AsyncSession = Depends(get_db),
) -> CorrelationRepository:
    return CorrelationRepository(db)


def get_validation_service(
    db: AsyncSession = Depends(get_db),
) -> ValidationService:
    return ValidationService(db)


def get_validation_repo(
    db: AsyncSession = Depends(get_db),
) -> ValidationRepository:
    return ValidationRepository(db)


# ---------------------------------------------------------------------
# Task basics
# ---------------------------------------------------------------------

@router.post("", response_model=TaskResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Create a new task")
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.create_task(payload)
    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse, summary="List tasks")
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


@router.get("/{task_id}", response_model=TaskResponse,
            summary="Get a single task")
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task {task_id} not found")
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------
# Task Understanding
# ---------------------------------------------------------------------

@router.post("/{task_id}/understand", response_model=TaskResponse,
             summary="Run task understanding on a task")
async def understand_task(
    task_id: UUID,
    service: TaskUnderstandingService = Depends(get_understanding_service),
) -> TaskResponse:
    try:
        task = await service.understand_task(task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task {task_id} not found")
    except TaskUnderstandingError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Task understanding failed: {e}")
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------

@router.post("/{task_id}/identify-requirements",
             response_model=IdentifyRequirementsResponse,
             summary="Identify requirements for a task")
async def identify_requirements(
    task_id: UUID,
    service: RequirementService = Depends(get_requirement_service),
    repo: RequirementRepository = Depends(get_requirement_repo),
) -> IdentifyRequirementsResponse:
    try:
        await service.identify_requirements(task_id)
    except RequirementError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    requirements = await repo.get_by_task_id(task_id)
    return IdentifyRequirementsResponse(
        task_id=task_id,
        total_requirements=len(requirements),
        identified_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{task_id}/requirements",
            response_model=TaskRequirementListResponse,
            summary="Get requirements for a task")
async def get_requirements(
    task_id: UUID,
    repo: RequirementRepository = Depends(get_requirement_repo),
) -> TaskRequirementListResponse:
    requirements = await repo.get_by_task_id(task_id)
    return TaskRequirementListResponse(
        requirements=[
            TaskRequirementResponse.model_validate(r) for r in requirements
        ],
        total=len(requirements),
    )


# ---------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------

@router.post("/{task_id}/retrieve", response_model=RunRetrievalResponse,
             summary="Run retrieval for a task")
async def run_retrieval(
    task_id: UUID,
    service: RetrievalService = Depends(get_retrieval_service),
) -> RunRetrievalResponse:
    try:
        summary = await service.retrieve_for_task(task_id)
    except RetrievalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    return RunRetrievalResponse(
        task_id=summary.task_id,
        total_retrieved=summary.total_retrieved,
        requirements_processed=summary.requirements_processed,
        requirements_skipped=summary.requirements_skipped,
        sources_used=summary.sources_used,
        run_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{task_id}/retrieved-records",
            response_model=RetrievedRecordListResponse,
            summary="Get retrieved records for a task")
async def get_retrieved_records(
    task_id: UUID,
    repo: RetrievedRecordRepository = Depends(get_retrieved_repo),
) -> RetrievedRecordListResponse:
    records = await repo.get_by_task_id(task_id)
    return RetrievedRecordListResponse(
        records=[RetrievedRecordResponse.model_validate(r) for r in records],
        total=len(records),
    )


# ---------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------

@router.post("/{task_id}/correlate", response_model=RunCorrelationResponse,
             summary="Run correlation for a task")
async def run_correlation(
    task_id: UUID,
    service: CorrelationService = Depends(get_correlation_service),
) -> RunCorrelationResponse:
    try:
        summary = await service.correlate_for_task(task_id)
    except CorrelationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    return RunCorrelationResponse(
        task_id=summary.task_id,
        total_correlations=summary.total_correlations,
        anchor_external_id=summary.anchor_external_id,
        basis_breakdown=summary.basis_breakdown,
        run_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{task_id}/correlations",
            response_model=CorrelationListResponse,
            summary="Get correlations for a task")
async def get_correlations(
    task_id: UUID,
    repo: CorrelationRepository = Depends(get_correlation_repo),
) -> CorrelationListResponse:
    rows = await repo.get_by_task_id(task_id)
    return CorrelationListResponse(
        correlations=[CorrelationResponse.model_validate(r) for r in rows],
        total=len(rows),
    )


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

@router.post("/{task_id}/validate", response_model=RunValidationResponse,
             summary="Run validation for a task")
async def run_validation(
    task_id: UUID,
    service: ValidationService = Depends(get_validation_service),
) -> RunValidationResponse:
    try:
        summary = await service.validate_for_task(task_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    return RunValidationResponse(
        task_id=summary.task_id,
        total_gaps=summary.total_gaps,
        total_inconsistencies=summary.total_inconsistencies,
        by_severity=summary.by_severity,
        run_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{task_id}/validations",
            response_model=ValidationListResponse,
            summary="Get validations for a task")
async def get_validations(
    task_id: UUID,
    repo: ValidationRepository = Depends(get_validation_repo),
) -> ValidationListResponse:
    rows = await repo.get_by_task_id(task_id)
    return ValidationListResponse(
        validations=[ValidationResponse.model_validate(r) for r in rows],
        total=len(rows),
    )


# ---------------------------------------------------------------------
# Context Workspace
# ---------------------------------------------------------------------

@router.get("/{task_id}/context", response_model=ContextWorkspaceResponse,
            summary="Aggregated context workspace for a task")
async def get_context_workspace(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service),
    req_repo: RequirementRepository = Depends(get_requirement_repo),
    ret_repo: RetrievedRecordRepository = Depends(get_retrieved_repo),
    corr_repo: CorrelationRepository = Depends(get_correlation_repo),
    val_repo: ValidationRepository = Depends(get_validation_repo),
) -> ContextWorkspaceResponse:
    task = await task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task {task_id} not found")
    requirements = await req_repo.get_by_task_id(task_id)
    retrieved = await ret_repo.get_by_task_id(task_id)
    correlations = await corr_repo.get_by_task_id(task_id)
    validations = await val_repo.get_by_task_id(task_id)
    return ContextWorkspaceResponse(
        task=TaskResponse.model_validate(task),
        requirements=[
            TaskRequirementResponse.model_validate(r) for r in requirements
        ],
        retrieved_records=[
            RetrievedRecordResponse.model_validate(r) for r in retrieved
        ],
        correlations=[
            CorrelationResponse.model_validate(c) for c in correlations
        ],
        validations=[
            ValidationResponse.model_validate(v) for v in validations
        ],
    )