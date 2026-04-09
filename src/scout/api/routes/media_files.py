import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.db.session import get_db
from scout.db.models.clip import Clip
from scout.db.models.job import Job
from scout.db.models.user import User
from scout.core.auth import hash_api_key

router = APIRouter()


async def _get_user_by_key(api_key: str, db: AsyncSession) -> User | None:
    """Authenticate user by API key (from header or query param)."""
    key_hash = hash_api_key(api_key)
    result = await db.execute(select(User).where(User.api_key_hash == key_hash))
    return result.scalar_one_or_none()


async def _auth_from_header_or_query(
    api_key: Optional[str] = Query(None, alias="key"),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, AsyncSession]:
    """Accept API key from X-API-Key header OR ?key= query param (for video tags)."""
    from fastapi import Request
    # Try query param first
    if api_key:
        user = await _get_user_by_key(api_key, db)
        if user:
            return user, db
    raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/jobs/{job_id}/video")
async def stream_job_video(
    job_id: str,
    variant: str = "edited",
    key: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Stream a job's video file. Pass API key as ?key= query param."""
    if not key:
        raise HTTPException(status_code=401, detail="API key required as ?key= parameter")

    user = await _get_user_by_key(key, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = job.edited_file_url if variant == "edited" else job.raw_file_url
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(file_path, media_type="video/mp4", filename=job.source_filename)


@router.get("/clips/{clip_id}/video")
async def stream_clip_video(
    clip_id: str,
    platform: str = "",
    key: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Stream a clip's video file. Pass API key as ?key= query param."""
    if not key:
        raise HTTPException(status_code=401, detail="API key required as ?key= parameter")

    user = await _get_user_by_key(key, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    result = await db.execute(
        select(Clip).where(Clip.id == clip_id, Clip.user_id == user.id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    file_path = clip.clip_file_url
    if platform and clip.platform_variants:
        file_path = clip.platform_variants.get(platform, file_path)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip file not found")

    return FileResponse(file_path, media_type="video/mp4", filename=f"{clip.title}.mp4")


@router.get("/clips/{clip_id}/thumbnail")
async def get_clip_thumbnail(
    clip_id: str,
    key: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Get a clip's thumbnail image."""
    if not key:
        raise HTTPException(status_code=401, detail="API key required")

    user = await _get_user_by_key(key, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    result = await db.execute(
        select(Clip).where(Clip.id == clip_id, Clip.user_id == user.id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if not clip.thumbnail_url or not os.path.exists(clip.thumbnail_url):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(clip.thumbnail_url, media_type="image/jpeg")
