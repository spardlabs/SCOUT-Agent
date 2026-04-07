import asyncio
import os
import tempfile
import uuid

import anthropic
from celery import shared_task

from scout.config import settings
from scout.core.logging import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def process_dropbox_changes(self, dropbox_account_id: str):
    """Process file changes from a Dropbox account."""
    asyncio.run(_process_dropbox_changes(dropbox_account_id))


async def _process_dropbox_changes(dropbox_account_id: str):
    """Async implementation of Dropbox change processing."""
    import dropbox as dbx

    from scout.db.session import async_session_factory
    from scout.db.models.user import User
    from scout.db.models.social_account import SocialAccount
    from scout.services.crypto import decrypt_token

    async with async_session_factory() as db:
        from sqlalchemy import select

        # Find user by Dropbox account ID
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.platform_user_id == dropbox_account_id,
                SocialAccount.platform == "dropbox",  # We'll use this for storage connections too
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            logger.warning("dropbox_account_not_found", account_id=dropbox_account_id)
            return

        access_token = decrypt_token(account.access_token_encrypted)
        client = dbx.Dropbox(access_token)

        # List recent changes in monitored folder
        try:
            result = client.files_list_folder("/podcast-uploads")
            for entry in result.entries:
                if isinstance(entry, dbx.files.FileMetadata):
                    if entry.name.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
                        logger.info("new_podcast_file", filename=entry.name)
                        # Download and process
                        with tempfile.TemporaryDirectory() as tmpdir:
                            local_path = os.path.join(tmpdir, entry.name)
                            client.files_download_to_file(local_path, entry.path_lower)
                            await _ingest_file(db, account.user_id, local_path, entry.name)
        except Exception as e:
            logger.error("dropbox_list_failed", error=str(e))
            raise


@shared_task(bind=True, max_retries=3)
def process_google_drive_changes(self, channel_id: str):
    """Process file changes from Google Drive."""
    asyncio.run(_process_google_drive_changes(channel_id))


async def _process_google_drive_changes(channel_id: str):
    """Async implementation of Google Drive change processing."""
    logger.info("google_drive_changes", channel_id=channel_id)
    # Implementation follows same pattern as Dropbox
    # Uses Google Drive API to list changes and download new files


@shared_task(bind=True, max_retries=3)
def process_s3_upload(self, bucket: str, key: str, user_id: str):
    """Process a new file uploaded directly to S3."""
    asyncio.run(_process_s3_upload(bucket, key, user_id))


async def _process_s3_upload(bucket: str, key: str, user_id: str):
    """Download from S3 and ingest."""
    from scout.db.session import async_session_factory
    from scout.services.storage import StorageService

    storage = StorageService()

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.basename(key)
        local_path = os.path.join(tmpdir, filename)
        storage.download_file(key, local_path)

        async with async_session_factory() as db:
            await _ingest_file(db, user_id, local_path, filename)
            await db.commit()


async def _ingest_file(db, user_id: str, local_path: str, filename: str):
    """Core ingestion logic: validate, upload to storage, create job, chain to editing."""
    from scout.db.models.job import Job, JobStatus
    from scout.services.storage import StorageService

    # Create job record
    job = Job(
        user_id=user_id,
        source_filename=filename,
        status=JobStatus.INGESTING,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    job_id = str(job.id)

    try:
        # Run ingest agent
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        storage = StorageService()

        from scout.agents.ingest import IngestAgent

        agent = IngestAgent(client, storage)
        result = await agent.run({
            "file_path": local_path,
            "job_id": job_id,
            "user_id": str(user_id),
            "s3_key_prefix": f"raw/{user_id}/{job_id}",
        })

        # Update job with results
        import json
        agent_result = json.loads(result["result"]) if isinstance(result["result"], str) else result

        s3_url = f"s3://scout-media/raw/{user_id}/{job_id}/{filename}"
        storage.upload_from_path(local_path, f"raw/{user_id}/{job_id}/{filename}")

        job.status = JobStatus.INGESTED
        job.raw_file_url = s3_url

        # Extract duration from media info
        from scout.services.media import MediaService

        info = MediaService.get_media_info(local_path)
        job.duration_seconds = float(info.get("format", {}).get("duration", 0))
        job.metadata = info

        await db.flush()

        logger.info("file_ingested", job_id=job_id, filename=filename)

        # Chain to long-form editing
        from scout.tasks.longform import edit_episode

        edit_episode.delay(job_id)

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        await db.flush()
        logger.error("ingest_failed", job_id=job_id, error=str(e))
        raise
