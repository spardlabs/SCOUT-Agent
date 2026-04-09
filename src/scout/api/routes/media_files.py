import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.db.models.clip import Clip
from scout.db.models.job import Job
from scout.db.models.user import User

router = APIRouter()

TEMP_DIR = os.path.join(tempfile.gettempdir(), "scout-uploads")


@router.get("/jobs/{job_id}/video")
async def stream_job_video(
    job_id: str,
    variant: str = "edited",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a job's video file (raw or edited)."""
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a clip's video file, optionally a platform-specific variant."""
    result = await db.execute(
        select(Clip).where(Clip.id == clip_id, Clip.user_id == user.id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Get platform variant or master clip
    file_path = clip.clip_file_url
    if platform and clip.platform_variants:
        file_path = clip.platform_variants.get(platform, file_path)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip file not found")

    return FileResponse(file_path, media_type="video/mp4", filename=f"{clip.title}.mp4")


@router.get("/clips/{clip_id}/thumbnail")
async def get_clip_thumbnail(
    clip_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a clip's thumbnail image."""
    result = await db.execute(
        select(Clip).where(Clip.id == clip_id, Clip.user_id == user.id)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if not clip.thumbnail_url or not os.path.exists(clip.thumbnail_url):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(clip.thumbnail_url, media_type="image/jpeg")
