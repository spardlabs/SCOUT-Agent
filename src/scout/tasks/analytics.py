import asyncio
from datetime import date, datetime, timedelta

import anthropic
from celery import shared_task

from scout.config import settings
from scout.core.logging import get_logger

logger = get_logger(__name__)


@shared_task
def collect_daily_metrics():
    """Collect metrics from all platforms for all posted content. Runs daily."""
    asyncio.run(_collect_daily_metrics())


async def _collect_daily_metrics():
    from sqlalchemy import select
    from scout.db.session import async_session_factory
    from scout.db.models.post import Post, PostStatus
    from scout.db.models.social_account import SocialAccount
    from scout.db.models.analytics import AnalyticsSnapshot
    from scout.services.crypto import decrypt_token

    async with async_session_factory() as db:
        # Get all posted content
        result = await db.execute(
            select(Post, SocialAccount)
            .join(SocialAccount, SocialAccount.id == Post.social_account_id)
            .where(Post.status == PostStatus.POSTED)
        )
        posts = result.all()

        for post, account in posts:
            try:
                access_token = decrypt_token(account.access_token_encrypted)
                from scout.tasks.posting import _get_platform_adapter

                adapter = _get_platform_adapter(
                    account.platform.value, access_token, account
                )
                metrics = await adapter.get_post_metrics(post.platform_post_id)

                snapshot = AnalyticsSnapshot(
                    post_id=post.id,
                    captured_at=datetime.utcnow(),
                    views=metrics.views,
                    likes=metrics.likes,
                    comments=metrics.comments,
                    shares=metrics.shares,
                    saves=metrics.saves,
                    watch_time_seconds=metrics.watch_time_seconds,
                    avg_watch_percentage=metrics.avg_watch_percentage,
                    raw_data=metrics.raw_data,
                )
                db.add(snapshot)

                logger.info(
                    "metrics_collected",
                    post_id=str(post.id),
                    platform=account.platform.value,
                    views=metrics.views,
                )
            except Exception as e:
                logger.error(
                    "metrics_collection_failed",
                    post_id=str(post.id),
                    error=str(e),
                )

        await db.commit()


@shared_task
def generate_weekly_reports():
    """Generate weekly performance reports for all users. Runs every Monday."""
    asyncio.run(_generate_weekly_reports())


async def _generate_weekly_reports():
    from sqlalchemy import select, distinct
    from scout.db.session import async_session_factory
    from scout.db.models.post import Post, PostStatus
    from scout.db.models.social_account import SocialAccount

    today = date.today()
    week_end = today - timedelta(days=today.weekday())  # Most recent Monday
    week_start = week_end - timedelta(days=7)

    async with async_session_factory() as db:
        # Find all users who had posts in the last week
        result = await db.execute(
            select(distinct(SocialAccount.user_id))
            .join(Post, Post.social_account_id == SocialAccount.id)
            .where(
                Post.status == PostStatus.POSTED,
                Post.posted_at >= datetime.combine(week_start, datetime.min.time()),
                Post.posted_at <= datetime.combine(week_end, datetime.max.time()),
            )
        )
        user_ids = [row[0] for row in result.all()]

        for user_id in user_ids:
            try:
                client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

                from scout.agents.analytics import AnalyticsAgent

                agent = AnalyticsAgent(client, db)

                # Run analytics agent to generate report
                agent_result = await agent.run({
                    "user_id": str(user_id),
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                })

                # Save the report
                import json
                try:
                    report_data = json.loads(agent_result["result"])
                    narrative = report_data.get("narrative", agent_result["result"])
                    metrics = report_data.get("metrics", {})
                except (json.JSONDecodeError, TypeError):
                    narrative = agent_result["result"]
                    metrics = {}

                await agent.save_report(
                    user_id=str(user_id),
                    week_start=week_start,
                    week_end=week_end,
                    report_data=metrics,
                    narrative=narrative,
                )

                logger.info("weekly_report_generated", user_id=str(user_id))

            except Exception as e:
                logger.error(
                    "report_generation_failed",
                    user_id=str(user_id),
                    error=str(e),
                )

        await db.commit()
