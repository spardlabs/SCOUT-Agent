import os
import tempfile

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.api.schemas.job import JobResponse
from scout.db.models.job import Job, JobStatus
from scout.db.models.user import User
from scout.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav"}


@router.post("", response_model=JobResponse, status_code=201)
async def upload_episode(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a raw podcast file to start the processing pipeline."""
    filename = file.filename or "upload.mp4"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Create job record
    job = Job(
        user_id=user.id,
        source_filename=filename,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    job_id = str(job.id)
    user_id = str(user.id)

    try:
        # Save file to local storage
        upload_dir = os.path.join(tempfile.gettempdir(), "scout-uploads", user_id, job_id)
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, filename)

        with open(local_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        file_size = os.path.getsize(local_path)
        job.raw_file_url = local_path
        job.file_metadata = {
            "file_size": file_size,
            "original_filename": filename,
            "extension": ext,
        }

        logger.info("file_uploaded", job_id=job_id, filename=filename, size_mb=round(file_size / (1024 * 1024), 2))

        # Trigger the processing pipeline in the background
        from scout.pipeline import process_episode

        background_tasks.add_task(_run_pipeline, job_id, user_id, local_path)

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        logger.error("upload_failed", job_id=job_id, error=str(e))

    await db.flush()
    await db.refresh(job)

    return JobResponse.model_validate(job)


async def _run_pipeline(job_id: str, user_id: str, file_path: str):
    """Wrapper to run the async pipeline from a background task."""
    from scout.pipeline import process_episode

    await process_episode(job_id, user_id, file_path)
