import httpx

from scout.core.logging import get_logger
from scout.services.social.base import MetricsResult, PostResult, SocialPlatform

logger = get_logger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class InstagramPlatform(SocialPlatform):
    def __init__(self, access_token: str, ig_user_id: str):
        self.access_token = access_token
        self.ig_user_id = ig_user_id

    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        **kwargs,
    ) -> PostResult:
        full_caption = f"{caption}\n\n{' '.join(f'#{h}' for h in hashtags)}"

        async with httpx.AsyncClient() as client:
            # For Reels, use the video URL approach
            # In production, upload to public URL first (e.g., S3 presigned)
            video_url = kwargs.get("video_url", "")

            # Step 1: Create media container
            container_resp = await client.post(
                f"{GRAPH_API_BASE}/{self.ig_user_id}/media",
                params={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": full_caption,
                    "access_token": self.access_token,
                },
            )
            container_id = container_resp.json().get("id")

            # Step 2: Publish the container
            publish_resp = await client.post(
                f"{GRAPH_API_BASE}/{self.ig_user_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": self.access_token,
                },
            )
            media_id = publish_resp.json().get("id")

            logger.info("instagram_reel_posted", media_id=media_id)
            return PostResult(
                platform_post_id=media_id,
                platform_post_url=f"https://www.instagram.com/reel/{media_id}/",
                raw_response=publish_resp.json(),
            )

    async def get_post_metrics(self, platform_post_id: str) -> MetricsResult:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/{platform_post_id}/insights",
                params={
                    "metric": "plays,likes,comments,shares,saved,ig_reels_avg_watch_time",
                    "access_token": self.access_token,
                },
            )
            data = resp.json()
            metrics = {}
            for item in data.get("data", []):
                metrics[item["name"]] = item["values"][0]["value"]

            return MetricsResult(
                views=metrics.get("plays", 0),
                likes=metrics.get("likes", 0),
                comments=metrics.get("comments", 0),
                shares=metrics.get("shares", 0),
                saves=metrics.get("saved", 0),
                watch_time_seconds=metrics.get("ig_reels_avg_watch_time"),
                raw_data=data,
            )

    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": "",  # Set from config
                    "client_secret": "",
                    "fb_exchange_token": refresh_token,
                },
            )
            data = resp.json()
            return {"access_token": data["access_token"], "refresh_token": data["access_token"]}
