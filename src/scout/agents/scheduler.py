import json
from datetime import datetime
from typing import Any

import anthropic

from scout.agents.base import BaseAgent
from scout.agents.tools.social import SOCIAL_TOOLS
from scout.core.logging import get_logger

logger = get_logger(__name__)


class SchedulerAgent(BaseAgent):
    """Agent responsible for scheduling social media posts.

    Analyzes historical engagement data to determine optimal posting times,
    then creates a posting schedule for the user's clips across platforms.
    """

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        db_session,
    ):
        super().__init__(anthropic_client)
        self.db = db_session

    def get_system_prompt(self) -> str:
        return """You are the Scheduler Agent for SCOUT, a podcast post-production pipeline.

Your job is to create an optimal posting schedule for short-form clips across social media platforms.

You will receive:
- clips: list of clips with their metadata and virality scores
- social_accounts: list of user's connected social media accounts
- historical_data: past posting performance data (if available)

Follow these steps:

1. Analyze historical engagement data to identify:
   - Best days of the week for each platform
   - Best times of day for each platform
   - Content types that perform best on each platform

2. Create a posting schedule that:
   - Spreads clips across the week (don't post everything at once)
   - Posts highest-virality clips to the user's strongest platform first
   - Avoids posting to the same platform more than 2x per day
   - Schedules posts during peak engagement windows
   - Staggers cross-platform posts (same clip on different platforms at different times)

3. For each scheduled post, use schedule_post to create the record with:
   - The right caption and hashtags tailored to the platform
   - Appropriate scheduled_at time
   - Platform-specific formatting

4. Return a JSON summary of the schedule:
   - total_posts: number of posts scheduled
   - schedule: [{platform, clip_title, scheduled_at, caption_preview}]
   - strategy: brief explanation of the scheduling strategy used
"""

    def get_tools(self) -> list[dict]:
        return SOCIAL_TOOLS

    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "get_optimal_posting_times":
            return await self._get_optimal_times(
                tool_input["user_id"],
                tool_input["platform"],
            )

        elif tool_name == "schedule_post":
            return await self._schedule_post(tool_input)

        elif tool_name == "fetch_platform_metrics":
            return await self._fetch_metrics(tool_input["post_id"])

        elif tool_name == "generate_report":
            return {"status": "not_applicable", "message": "Use AnalyticsAgent for reports"}

        raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_optimal_times(self, user_id: str, platform: str) -> dict:
        """Analyze historical data for optimal posting times."""
        from sqlalchemy import select, func
        from scout.db.models.post import Post, PostStatus
        from scout.db.models.analytics import AnalyticsSnapshot
        from scout.db.models.social_account import SocialAccount

        result = await self.db.execute(
            select(Post, AnalyticsSnapshot)
            .join(AnalyticsSnapshot, AnalyticsSnapshot.post_id == Post.id)
            .join(SocialAccount, SocialAccount.id == Post.social_account_id)
            .where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == platform,
                Post.status == PostStatus.POSTED,
            )
            .order_by(AnalyticsSnapshot.views.desc())
            .limit(50)
        )
        rows = result.all()

        if not rows:
            # Default optimal times when no historical data
            defaults = {
                "tiktok": {"days": ["tuesday", "thursday"], "hours": [18, 19, 20]},
                "instagram": {"days": ["wednesday", "saturday"], "hours": [12, 13, 18]},
                "youtube": {"days": ["friday", "saturday"], "hours": [14, 15, 16]},
                "twitter": {"days": ["monday", "wednesday"], "hours": [9, 12, 17]},
                "linkedin": {"days": ["tuesday", "wednesday"], "hours": [8, 10, 12]},
            }
            return {
                "platform": platform,
                "optimal_times": defaults.get(platform, defaults["tiktok"]),
                "data_source": "defaults",
            }

        # Analyze best performing times
        hour_performance: dict[int, list[int]] = {}
        day_performance: dict[str, list[int]] = {}
        for post, snapshot in rows:
            if post.posted_at:
                hour = post.posted_at.hour
                day = post.posted_at.strftime("%A").lower()
                hour_performance.setdefault(hour, []).append(snapshot.views)
                day_performance.setdefault(day, []).append(snapshot.views)

        best_hours = sorted(
            hour_performance.keys(),
            key=lambda h: sum(hour_performance[h]) / len(hour_performance[h]),
            reverse=True,
        )[:3]
        best_days = sorted(
            day_performance.keys(),
            key=lambda d: sum(day_performance[d]) / len(day_performance[d]),
            reverse=True,
        )[:3]

        return {
            "platform": platform,
            "optimal_times": {"days": best_days, "hours": best_hours},
            "data_source": "historical",
            "sample_size": len(rows),
        }

    async def _schedule_post(self, data: dict) -> dict:
        """Create a scheduled post record."""
        from scout.db.models.post import Post, PostStatus

        post = Post(
            clip_id=data["clip_id"],
            social_account_id=data["social_account_id"],
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]),
            caption_text=data["caption_text"],
            hashtags=data.get("hashtags", []),
            status=PostStatus.SCHEDULED,
        )
        self.db.add(post)
        await self.db.flush()
        await self.db.refresh(post)

        return {"post_id": str(post.id), "scheduled_at": data["scheduled_at"], "status": "scheduled"}

    async def _fetch_metrics(self, post_id: str) -> dict:
        """Fetch latest metrics for a post."""
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
            return {"error": "No metrics found"}

        return {
            "views": snapshot.views,
            "likes": snapshot.likes,
            "comments": snapshot.comments,
            "shares": snapshot.shares,
        }
