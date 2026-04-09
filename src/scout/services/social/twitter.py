import httpx

from scout.core.logging import get_logger
from scout.services.social.base import MetricsResult, PostResult, SocialPlatform

logger = get_logger(__name__)

TWITTER_API_BASE = "https://api.twitter.com/2"
TWITTER_UPLOAD_BASE = "https://upload.twitter.com/1.1"


class TwitterPlatform(SocialPlatform):
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
        full_text = f"{caption} {' '.join(f'#{h}' for h in hashtags)}"

        async with httpx.AsyncClient() as client:
            # Step 1: Upload media via chunked upload
            # INIT
            import os
            file_size = os.path.getsize(video_path)
            init_resp = await client.post(
                f"{TWITTER_UPLOAD_BASE}/media/upload.json",
                headers=self.headers,
                data={
                    "command": "INIT",
                    "total_bytes": file_size,
                    "media_type": "video/mp4",
                    "media_category": "tweet_video",
                },
            )
            media_id = init_resp.json()["media_id_string"]

            # APPEND
            with open(video_path, "rb") as f:
                chunk_index = 0
                while True:
                    chunk = f.read(5 * 1024 * 1024)  # 5MB chunks
                    if not chunk:
                        break
                    await client.post(
                        f"{TWITTER_UPLOAD_BASE}/media/upload.json",
                        headers=self.headers,
                        data={"command": "APPEND", "media_id": media_id, "segment_index": chunk_index},
                        files={"media_data": chunk},
                    )
                    chunk_index += 1

            # FINALIZE
            await client.post(
                f"{TWITTER_UPLOAD_BASE}/media/upload.json",
                headers=self.headers,
                data={"command": "FINALIZE", "media_id": media_id},
            )

            # Step 2: Create tweet with media
            tweet_resp = await client.post(
                f"{TWITTER_API_BASE}/tweets",
                headers=self.headers,
                json={"text": full_text[:280], "media": {"media_ids": [media_id]}},
            )
            tweet_data = tweet_resp.json()
            tweet_id = tweet_data["data"]["id"]

            logger.info("twitter_video_posted", tweet_id=tweet_id)
            return PostResult(
                platform_post_id=tweet_id,
                platform_post_url=f"https://x.com/i/status/{tweet_id}",
                raw_response=tweet_data,
            )

    async def get_post_metrics(self, platform_post_id: str) -> MetricsResult:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{TWITTER_API_BASE}/tweets/{platform_post_id}",
                headers=self.headers,
                params={"tweet.fields": "public_metrics"},
            )
            data = resp.json()
            metrics = data.get("data", {}).get("public_metrics", {})

            return MetricsResult(
                views=metrics.get("impression_count", 0),
                likes=metrics.get("like_count", 0),
                comments=metrics.get("reply_count", 0),
                shares=metrics.get("retweet_count", 0),
                raw_data=data,
            )

    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        from scout.config import settings

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TWITTER_API_BASE}/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.twitter_api_key,
                },
            )
            data = resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
            }
