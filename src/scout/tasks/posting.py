import asyncio
import json
import os
import tempfile
from datetime import datetime

import anthropic
from celery import shared_task

from scout.config import settings
from scout.core.logging import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2)
def schedule_clips(self, job_id: str):
    """Create a posting schedule for clips from a job."""
    asyncio.run(_schedule_clips(job_id))


async def _schedule_clips(job_id: str):
    from sqlalchemy import select
    from scout.db.session import async_session_factory
    from scout.db.models.job import Job, JobStatus
    from scout.db.models.clip import Clip
    from scout.db.models.social_account import SocialAccount

    async with async_session_factory() as db:
        # Load job
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        job.status = JobStatus.SCHEDULING
        await db.flush()

        # Load clips
        result = await db.execute(
            select(Clip).where(Clip.job_id == job_id).order_by(Clip.virality_score.desc())
        )
        clips = result.scalars().all()

        # Load social accounts
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == job.user_id,
                SocialAccount.is_active == True,
            )
        )
        accounts = result.scalars().all()

        if not clips or not accounts:
            job.status = JobStatus.COMPLETE
            await db.flush()
            await db.commit()
            return

        try:
            # Run scheduler agent
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            from scout.agents.scheduler import SchedulerAgent

            agent = SchedulerAgent(client, db)
            await agent.run({
                "clips": [
                    {
                        "id": str(c.id),
                        "title": c.title,
                        "description": c.description,
                        "virality_score": c.virality_score,
                        "topics": c.topics,
                        "duration_seconds": c.duration_seconds,
                        "platform_variants": c.platform_variants,
                    }
                    for c in clips
                ],
                "social_accounts": [
                    {
                        "id": str(a.id),
                        "platform": a.platform.value,
                        "username": a.platform_username,
                    }
                    for a in accounts
                ],
                "user_id": str(job.user_id),
            })

            job.status = JobStatus.COMPLETE
            job.completed_at = datetime.utcnow()
            await db.flush()
            await db.commit()

            logger.info("clips_scheduled", job_id=job_id)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.flush()
            await db.commit()
            logger.error("scheduling_failed", job_id=job_id, error=str(e))
            raise


@shared_task
def execute_due_posts():
    """Execute all posts that are due for publishing. Runs every minute via Celery Beat."""
    asyncio.run(_execute_due_posts())


async def _execute_due_posts():
    from sqlalchemy import select
    from scout.db.session import async_session_factory
    from scout.db.models.post import Post, PostStatus
    from scout.db.models.clip import Clip
    from scout.db.models.social_account import SocialAccount
    from scout.services.crypto import decrypt_token
    from scout.services.storage import StorageService

    now = datetime.utcnow()
    storage = StorageService()

    async with async_session_factory() as db:
        # Find due posts
        result = await db.execute(
            select(Post, Clip, SocialAccount)
            .join(Clip, Clip.id == Post.clip_id)
            .join(SocialAccount, SocialAccount.id == Post.social_account_id)
            .where(Post.scheduled_at <= now, Post.status == PostStatus.SCHEDULED)
        )
        due_posts = result.all()

        for post, clip, account in due_posts:
            try:
                post.status = PostStatus.POSTING
                await db.flush()

                # Download the clip variant for this platform
                platform = account.platform.value
                variant_url = (clip.platform_variants or {}).get(platform, clip.clip_file_url)

                with tempfile.TemporaryDirectory() as tmpdir:
                    video_path = os.path.join(tmpdir, "clip.mp4")
                    storage.download_file(storage.key_from_url(variant_url), video_path)

                    access_token = decrypt_token(account.access_token_encrypted)

                    # Get the right platform adapter
                    adapter = _get_platform_adapter(platform, access_token, account)

                    # Post the video
                    post_result = await adapter.post_video(
                        video_path=video_path,
                        caption=post.caption_text,
                        hashtags=post.hashtags,
                    )

                    post.platform_post_id = post_result.platform_post_id
                    post.platform_post_url = post_result.platform_post_url
                    post.posted_at = datetime.utcnow()
                    post.status = PostStatus.POSTED

                logger.info(
                    "post_published",
                    post_id=str(post.id),
                    platform=platform,
                )

            except Exception as e:
                post.status = PostStatus.FAILED
                post.error_message = str(e)
                logger.error(
                    "post_failed",
                    post_id=str(post.id),
                    platform=platform,
                    error=str(e),
                )

            await db.flush()
        await db.commit()


def _get_platform_adapter(platform: str, access_token: str, account):
    """Get the appropriate social media platform adapter."""
    if platform == "tiktok":
        from scout.services.social.tiktok import TikTokPlatform
        return TikTokPlatform(access_token)
    elif platform == "instagram":
        from scout.services.social.instagram import InstagramPlatform
        return InstagramPlatform(access_token, account.platform_user_id)
    elif platform == "youtube":
        from scout.services.social.youtube import YouTubePlatform
        return YouTubePlatform(access_token)
    elif platform == "twitter":
        from scout.services.social.twitter import TwitterPlatform
        return TwitterPlatform(access_token)
    elif platform == "linkedin":
        from scout.services.social.linkedin import LinkedInPlatform
        return LinkedInPlatform(access_token, f"urn:li:person:{account.platform_user_id}")
    else:
        raise ValueError(f"Unsupported platform: {platform}")
