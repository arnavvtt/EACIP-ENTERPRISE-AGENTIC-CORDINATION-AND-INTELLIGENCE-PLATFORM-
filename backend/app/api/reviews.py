"""
Human Review API routes.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories import PackageRepository, ReviewRepository
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/tasks", tags=["reviews"])


def get_review_repo(db: AsyncSession = Depends(get_db)) -> ReviewRepository:
    return ReviewRepository(db)

def get_package_repo(db: AsyncSession = Depends(get_db)) -> PackageRepository:
    return PackageRepository(db)


@router.post("/{task_id}/review", response_model=ReviewResponse)
async def submit_review(
    task_id: UUID,
    payload: ReviewCreate,
    review_repo: ReviewRepository = Depends(get_review_repo),
    package_repo: PackageRepository = Depends(get_package_repo),
    db: AsyncSession = Depends(get_db),
):
    # 1. Get the latest package for this task
    pkg = await package_repo.get_latest_for_task(task_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="No package found for this task.")

    if payload.decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'.")

    # 2. Create the review record
    review = await review_repo.create(
        task_id=task_id,
        package_id=pkg.id,
        decision=payload.decision,
        comments=payload.comments,
    )

    # 3. Update the package status
    pkg.status = payload.decision
    await db.commit()
    await db.refresh(review)

    return ReviewResponse.model_validate(review)