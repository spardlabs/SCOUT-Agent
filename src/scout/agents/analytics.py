import json
from datetime import date, datetime, timedelta
from typing import Any

import anthropic

from scout.agents.base import BaseAgent
from scout.agents.tools.social import SOCIAL_TOOLS
from scout.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsAgent(BaseAgent):
    """Agent responsible for collecting metrics and generating weekly reports.

    Pulls metrics from social platform APIs, identifies trends,
    and generates actionable insights for podcast creators.
    """

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        db_session,
    ):
        super().__init__(anthropic_client)
        self.db = db_session

    def get_system_prompt(self) -> str:
        return """You are the Analytics Agent for SCOUT, a podcast post-production pipeline.

Your job is to analyze social media performance and generate insightful weekly reports.

You will receive:
- user_id: the user to generate a report for
- week_start and week_end: the reporting period
- metrics_data: aggregated metrics from all platforms

Analyze the data and generate a report that includes:

1. PERFORMANCE SUMMARY:
   - Total views, likes, comments, shares across all platforms
   - Comparison to previous week (if available)
   - Best performing clip and why

2. PLATFORM BREAKDOWN:
   - Per-platform metrics and trends
   - Which platform is driving the most engagement
   - Platform-specific recommendations

3. CONTENT INSIGHTS:
   - Which topics/themes resonated most
   - What clip characteristics (length, style, hook) performed best
   - Content gaps or opportunities

4. ACTIONABLE RECOMMENDATIONS:
   - Specific suggestions for next week's content
   - Posting schedule adjustments based on data
   - Growth strategies

5. GROWTH METRICS:
   - Follower changes across platforms
   - Engagement rate trends
   - Audience growth velocity

Write in a friendly, data-driven tone. Use specific numbers. Be concise but insightful.
Return the narrative as a string and the structured data as a JSON object.
"""

    def get_tools(self) -> list[dict]:
        return SOCIAL_TOOLS

    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "fetch_platform_metrics":
            return await self._fetch_metrics(tool_input["post_id"])

        elif tool_name == "generate_report":
            return await self._generate_report_data(
                tool_input["user_id"],
                tool_input["week_start"],
                tool_input["week_end"],
            )

        elif tool_name == "get_optimal_posting_times":
            return {"message": "Use SchedulerAgent for posting time optimization"}

        elif tool_name == "schedule_post":
            return {"message": "Use SchedulerAgent for scheduling"}

        raise ValueError(f"Unknown tool: {tool_name}")

    async def _fetch_metrics(self, post_id: str) -> dict:
        """Fetch latest metrics snapshot for a post."""
        from sqlalchemy import select
        from scout.db.models.analytics import AnalyticsSnapshot

        result = await self.db.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.post_id == post_id)
            .order_by(AnalyticsSnapshot.captured_at.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return {"error": "No metrics available"}

        return {
            "views": snapshot.views,
            "likes": snapshot.likes,
            "comments": snapshot.comments,
            "shares": snapshot.shares,
            "saves": snapshot.saves,
            "watch_time_seconds": snapshot.watch_time_seconds,
            "avg_watch_percentage": snapshot.avg_watch_percentage,
            "follower_delta": snapshot.follower_delta,
        }

    async def _generate_report_data(
        self, user_id: str, week_start: str, week_end: str
    ) -> dict:
        """Aggregate metrics for the reporting period."""
        from sqlalchemy import select, func
        from scout.db.models.post import Post, PostStatus
        from scout.db.models.clip import Clip
        from scout.db.models.analytics import AnalyticsSnapshot
        from scout.db.models.social_account import SocialAccount

        start = datetime.fromisoformat(week_start)
        end = datetime.fromisoformat(week_end)

        # Get all posts from this period
        result = await self.db.execute(
            select(Post, Clip, SocialAccount)
            .join(Clip, Clip.id == Post.clip_id)
            .join(SocialAccount, SocialAccount.id == Post.social_account_id)
            .where(
                SocialAccount.user_id == user_id,
                Post.posted_at >= start,
                Post.posted_at <= end,
                Post.status == PostStatus.POSTED,
            )
        )
        posts = result.all()

        # Aggregate metrics
        platform_metrics: dict[str, dict] = {}
        clip_metrics: list[dict] = []
        total = {"views": 0, "likes": 0, "comments": 0, "shares": 0}

        for post, clip, account in posts:
            # Get latest snapshot for each post
            snap_result = await self.db.execute(
                select(AnalyticsSnapshot)
                .where(AnalyticsSnapshot.post_id == post.id)
                .order_by(AnalyticsSnapshot.captured_at.desc())
                .limit(1)
            )
            snapshot = snap_result.scalar_one_or_none()
            if not snapshot:
                continue

            platform = account.platform.value
            if platform not in platform_metrics:
                platform_metrics[platform] = {
                    "views": 0, "likes": 0, "comments": 0, "shares": 0, "posts": 0,
                }

            for metric in ["views", "likes", "comments", "shares"]:
                val = getattr(snapshot, metric, 0)
                platform_metrics[platform][metric] += val
                total[metric] += val
            platform_metrics[platform]["posts"] += 1

            clip_metrics.append({
                "title": clip.title,
                "platform": platform,
                "views": snapshot.views,
                "likes": snapshot.likes,
                "engagement_rate": (
                    (snapshot.likes + snapshot.comments + snapshot.shares) / max(snapshot.views, 1)
                ),
                "topics": clip.topics,
            })

        # Sort clips by engagement
        clip_metrics.sort(key=lambda c: c["engagement_rate"], reverse=True)

        return {
            "period": {"start": week_start, "end": week_end},
            "total_metrics": total,
            "platform_breakdown": platform_metrics,
            "top_clips": clip_metrics[:5],
            "total_posts": len(posts),
        }

    async def save_report(
        self, user_id: str, week_start: date, week_end: date,
        report_data: dict, narrative: str,
    ) -> str:
        """Save a generated weekly report to the database."""
        from scout.db.models.analytics import WeeklyReport

        report = WeeklyReport(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            report_data=report_data,
            narrative=narrative,
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)

        logger.info("weekly_report_saved", user_id=user_id, report_id=str(report.id))
        return str(report.id)
