import os
import tempfile
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.api.schemas.job import JobResponse
from scout.db.models.job import Job, JobStatus
from scout.db.models.user import User
from scout.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB


@router.post("", response_model=JobResponse, status_code=201)
async def upload_episode(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a raw podcast video file to start the processing pipeline."""
    # Validate file extension
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

    try:
        # Save file to local temp storage
        upload_dir = os.path.join(tempfile.gettempdir(), "scout-uploads", str(user.id), job_id)
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, filename)

        with open(local_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)

        file_size = os.path.getsize(local_path)
        job.status = JobStatus.INGESTED
        job.raw_file_url = local_path
        job.file_metadata = {
            "file_size": file_size,
            "original_filename": filename,
            "extension": ext,
        }

        logger.info(
            "file_uploaded",
            job_id=job_id,
            filename=filename,
            size_mb=round(file_size / (1024 * 1024), 2),
        )

        # In production, this would upload to S3 and trigger the ingest pipeline:
        # from scout.tasks.ingest import process_s3_upload
        # process_s3_upload.delay(bucket, key, str(user.id))

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        logger.error("upload_failed", job_id=job_id, error=str(e))

    await db.flush()
    await db.refresh(job)

    return JobResponse.model_validate(job)
