from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.api.schemas.job import JobListResponse, JobResponse
from scout.db.models.job import Job
from scout.db.models.user import User

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count()).select_from(Job).where(Job.user_id == user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Job)
        .where(Job.user_id == user.id)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)
