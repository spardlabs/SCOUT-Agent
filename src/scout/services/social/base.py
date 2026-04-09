from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PostResult:
    platform_post_id: str
    platform_post_url: str
    raw_response: dict[str, Any]


@dataclass
class MetricsResult:
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int | None = None
    watch_time_seconds: float | None = None
    avg_watch_percentage: float | None = None
    raw_data: dict[str, Any] | None = None


class SocialPlatform(ABC):
    """Abstract base class for social media platform integrations."""

    @abstractmethod
    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        **kwargs,
    ) -> PostResult:
        """Upload and post a video to the platform."""

    @abstractmethod
    async def get_post_metrics(self, platform_post_id: str) -> MetricsResult:
        """Fetch current metrics for a posted video."""

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        """Refresh an expired OAuth token. Returns new access/refresh tokens."""
