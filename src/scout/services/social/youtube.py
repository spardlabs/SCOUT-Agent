from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from scout.core.logging import get_logger
from scout.services.social.base import MetricsResult, PostResult, SocialPlatform

logger = get_logger(__name__)


class YouTubePlatform(SocialPlatform):
    def __init__(self, access_token: str):
        self.access_token = access_token

    def _get_service(self):
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=self.access_token)
        return build("youtube", "v3", credentials=credentials)

    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        **kwargs,
    ) -> PostResult:
        service = self._get_service()
        tags = hashtags[:30]  # YouTube limit

        body = {
            "snippet": {
                "title": kwargs.get("title", caption[:100]),
                "description": f"{caption}\n\n{' '.join(f'#{h}' for h in tags)}",
                "tags": tags,
                "categoryId": kwargs.get("category_id", "22"),  # People & Blogs
            },
            "status": {
                "privacyStatus": kwargs.get("privacy", "public"),
                "selfDeclaredMadeForKids": False,
            },
        }

        # Mark as Short if under 60 seconds
        if kwargs.get("is_short", True):
            body["snippet"]["title"] = f"{body['snippet']['title']} #Shorts"

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()

        video_id = response["id"]
        logger.info("youtube_video_posted", video_id=video_id)

        return PostResult(
            platform_post_id=video_id,
            platform_post_url=f"https://youtube.com/shorts/{video_id}",
            raw_response=response,
        )

    async def get_post_metrics(self, platform_post_id: str) -> MetricsResult:
        service = self._get_service()
        response = service.videos().list(
            part="statistics",
            id=platform_post_id,
        ).execute()

        stats = response.get("items", [{}])[0].get("statistics", {})
        return MetricsResult(
            views=int(stats.get("viewCount", 0)),
            likes=int(stats.get("likeCount", 0)),
            comments=int(stats.get("commentCount", 0)),
            shares=0,  # YouTube doesn't expose share count via API
            raw_data=response,
        )

    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        from scout.config import settings
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            data = resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": refresh_token,
            }
