from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.api.schemas.clip import ClipListResponse, ClipResponse
from scout.db.models.clip import Clip
from scout.db.models.user import User

router = APIRouter()


@router.get("", response_model=ClipListResponse)
async def list_clips(
    job_id: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Clip).where(Clip.user_id == user.id)
    count_query = select(func.count()).select_from(Clip).where(Clip.user_id == user.id)

    if job_id:
        query = query.where(Clip.job_id == job_id)
        count_query = count_query.where(Clip.job_id == job_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Clip.virality_score.desc()).offset(skip).limit(limit)
    )
    clips = result.scalars().all()

    return ClipListResponse(
        clips=[ClipResponse.model_validate(c) for c in clips],
        total=total,
    )


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    clip_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Clip).where(Clip.id == clip_id, Clip.user_id == user.id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return ClipResponse.model_validate(clip)
