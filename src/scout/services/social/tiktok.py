import httpx

from scout.core.logging import get_logger
from scout.services.social.base import MetricsResult, PostResult, SocialPlatform

logger = get_logger(__name__)

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokPlatform(SocialPlatform):
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        **kwargs,
    ) -> PostResult:
        async with httpx.AsyncClient() as client:
            # Step 1: Initialize upload
            init_resp = await client.post(
                f"{TIKTOK_API_BASE}/post/publish/inbox/video/init/",
                headers=self.headers,
                json={
                    "post_info": {
                        "title": caption,
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": 0,  # Will be set from file
                    },
                },
            )
            init_data = init_resp.json()
            upload_url = init_data.get("data", {}).get("upload_url", "")
            publish_id = init_data.get("data", {}).get("publish_id", "")

            # Step 2: Upload video file
            with open(video_path, "rb") as f:
                await client.put(upload_url, content=f.read(), headers={
                    "Content-Type": "video/mp4",
                })

            logger.info("tiktok_video_posted", publish_id=publish_id)
            return PostResult(
                platform_post_id=publish_id,
                platform_post_url=f"https://www.tiktok.com/@user/video/{publish_id}",
                raw_response=init_data,
            )

    async def get_post_metrics(self, platform_post_id: str) -> MetricsResult:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TIKTOK_API_BASE}/video/query/",
                headers=self.headers,
                json={
                    "filters": {"video_ids": [platform_post_id]},
                    "fields": ["like_count", "comment_count", "share_count", "view_count"],
                },
            )
            data = resp.json()
            videos = data.get("data", {}).get("videos", [{}])
            video = videos[0] if videos else {}

            return MetricsResult(
                views=video.get("view_count", 0),
                likes=video.get("like_count", 0),
                comments=video.get("comment_count", 0),
                shares=video.get("share_count", 0),
                raw_data=data,
            )

    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        from scout.config import settings

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TIKTOK_API_BASE}/oauth/token/",
                data={
                    "client_key": settings.tiktok_client_key,
                    "client_secret": settings.tiktok_client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
            data = resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
            }
