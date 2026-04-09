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
def generate_clips(self, job_id: str):
    """Generate short-form clips from an edited podcast episode."""
    asyncio.run(_generate_clips(job_id))


async def _generate_clips(job_id: str):
    from sqlalchemy import select
    from scout.db.session import async_session_factory
    from scout.db.models.job import Job, JobStatus
    from scout.db.models.clip import Clip, ClipStatus
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

        # Load profile
        result = await db.execute(
            select(EditingProfile).where(EditingProfile.user_id == job.user_id)
        )
        profile = result.scalar_one_or_none()

        job.status = JobStatus.CLIPPING
        await db.flush()

        try:
            with tempfile.TemporaryDirectory() as work_dir:
                # Download edited video
                edited_key = storage.key_from_url(job.edited_file_url)
                video_path = os.path.join(work_dir, "edited.mp4")
                storage.download_file(edited_key, video_path)

                # Download transcript
                transcript = {}
                if job.transcript_url:
                    transcript_key = storage.key_from_url(job.transcript_url)
                    transcript_path = os.path.join(work_dir, "transcript.json")
                    storage.download_file(transcript_key, transcript_path)
                    with open(transcript_path) as f:
                        transcript = json.load(f)

                # Build profile context
                profile_data = {}
                if profile:
                    profile_data = {
                        "topics": profile.topics,
                        "virality_preferences": profile.virality_preferences,
                        "target_platforms": profile.target_platforms,
                        "clip_length_range": profile.clip_length_range,
                        "caption_style": profile.caption_style,
                        "brand_color_primary": profile.brand_color_primary,
                    }

                # Run short-form clip agent
                client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

                from scout.agents.shortform import ShortFormClipAgent

                agent = ShortFormClipAgent(client, storage, work_dir)
                agent_result = await agent.run({
                    "video_path": video_path,
                    "transcript": transcript,
                    "profile": profile_data,
                    "job_id": job_id,
                    "user_id": str(job.user_id),
                    "work_dir": work_dir,
                })

                # Parse agent result and create clip records
                try:
                    clips_data = json.loads(agent_result["result"])
                    if isinstance(clips_data, dict):
                        clips_data = clips_data.get("clips", [])
                except (json.JSONDecodeError, TypeError):
                    clips_data = []

                for clip_data in clips_data:
                    clip = Clip(
                        job_id=job.id,
                        user_id=job.user_id,
                        title=clip_data.get("title", "Untitled Clip"),
                        description=clip_data.get("description", ""),
                        start_time_seconds=clip_data.get("start_time_seconds", 0),
                        end_time_seconds=clip_data.get("end_time_seconds", 0),
                        duration_seconds=clip_data.get("end_time_seconds", 0) - clip_data.get("start_time_seconds", 0),
                        clip_file_url=clip_data.get("clip_file_url", ""),
                        thumbnail_url=clip_data.get("thumbnail_url"),
                        platform_variants=clip_data.get("platform_variants"),
                        virality_score=clip_data.get("virality_score", 0.0),
                        topics=clip_data.get("topics", []),
                        transcript_text=clip_data.get("transcript_text", ""),
                        status=ClipStatus.GENERATED,
                    )
                    db.add(clip)

                job.status = JobStatus.CLIPPED
                await db.flush()
                await db.commit()

                logger.info(
                    "clips_generated",
                    job_id=job_id,
                    clip_count=len(clips_data),
                )

                # Chain to scheduling
                from scout.tasks.posting import schedule_clips

                schedule_clips.delay(job_id)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.flush()
            await db.commit()
            logger.error("clipping_failed", job_id=job_id, error=str(e))
            raise
