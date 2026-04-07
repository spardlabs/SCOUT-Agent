import asyncio
import json
import os
import tempfile

import anthropic
from celery import shared_task

from scout.config import settings
from scout.core.logging import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def edit_episode(self, job_id: str):
    """Edit a podcast episode based on user's editing profile."""
    asyncio.run(_edit_episode(job_id))


async def _edit_episode(job_id: str):
    from datetime import datetime

    from sqlalchemy import select
    from scout.db.session import async_session_factory
    from scout.db.models.job import Job, JobStatus
    from scout.db.models.profile import EditingProfile
    from scout.services.storage import StorageService

    storage = StorageService()

    async with async_session_factory() as db:
        # Load job
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error("job_not_found", job_id=job_id)
            return

        # Load user profile
        result = await db.execute(
            select(EditingProfile).where(EditingProfile.user_id == job.user_id)
        )
        profile = result.scalar_one_or_none()

        job.status = JobStatus.EDITING
        job.started_at = datetime.utcnow()
        await db.flush()

        try:
            with tempfile.TemporaryDirectory() as work_dir:
                # Download raw file
                raw_key = storage.key_from_url(job.raw_file_url)
                raw_path = os.path.join(work_dir, "raw.mp4")
                storage.download_file(raw_key, raw_path)

                # Build profile context for the agent
                profile_data = {}
                if profile:
                    profile_data = {
                        "silence_threshold_ms": profile.silence_threshold_ms,
                        "silence_action": profile.silence_action,
                        "target_lufs": profile.target_lufs,
                        "editing_style": profile.editing_style,
                        "intro_asset_url": profile.intro_asset_url,
                        "outro_asset_url": profile.outro_asset_url,
                        "logo_asset_url": profile.logo_asset_url,
                        "brand_color_primary": profile.brand_color_primary,
                        "caption_style": profile.caption_style,
                    }

                # Run long-form editing agent
                client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

                from scout.agents.longform import LongFormEditAgent

                agent = LongFormEditAgent(client, storage, work_dir)
                agent_result = await agent.run({
                    "file_path": raw_path,
                    "profile": profile_data,
                    "job_id": job_id,
                    "user_id": str(job.user_id),
                    "work_dir": work_dir,
                })

                # Upload edited file
                edited_path = os.path.join(work_dir, "edited.mp4")
                if not os.path.exists(edited_path):
                    # Agent may have used a different output name
                    for f in os.listdir(work_dir):
                        if "edited" in f or "normalized" in f or "final" in f:
                            edited_path = os.path.join(work_dir, f)
                            break

                edited_key = f"edited/{job.user_id}/{job_id}/edited.mp4"
                edited_url = storage.upload_from_path(edited_path, edited_key)

                # Upload transcript
                transcript_path = os.path.join(work_dir, "transcript.json")
                if os.path.exists(transcript_path):
                    transcript_key = f"transcripts/{job.user_id}/{job_id}/transcript.json"
                    transcript_url = storage.upload_from_path(
                        transcript_path, transcript_key, "application/json"
                    )
                    job.transcript_url = transcript_url

                # Update job
                job.status = JobStatus.EDITED
                job.edited_file_url = edited_url
                await db.flush()
                await db.commit()

                logger.info("episode_edited", job_id=job_id)

                # Chain to short-form clipping
                from scout.tasks.shortform import generate_clips

                generate_clips.delay(job_id)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.flush()
            await db.commit()
            logger.error("edit_failed", job_id=job_id, error=str(e))
            raise
