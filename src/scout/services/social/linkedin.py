import httpx

from scout.core.logging import get_logger
from scout.services.social.base import MetricsResult, PostResult, SocialPlatform

logger = get_logger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInPlatform(SocialPlatform):
    def __init__(self, access_token: str, person_urn: str):
        self.access_token = access_token
        self.person_urn = person_urn
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        **kwargs,
    ) -> PostResult:
        full_text = f"{caption}\n\n{' '.join(f'#{h}' for h in hashtags)}"

        async with httpx.AsyncClient() as client:
            # Step 1: Register upload
            register_resp = await client.post(
                f"{LINKEDIN_API_BASE}/assets?action=registerUpload",
                headers=self.headers,
                json={
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                        "owner": self.person_urn,
                        "serviceRelationships": [
                            {
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent",
                            }
                        ],
                    }
                },
            )
            register_data = register_resp.json()
            asset = register_data["value"]["asset"]
            upload_url = register_data["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]

            # Step 2: Upload video
            with open(video_path, "rb") as f:
                await client.put(upload_url, content=f.read(), headers={
                    "Authorization": f"Bearer {self.access_token}",
                })

            # Step 3: Create post
            post_resp = await client.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                headers=self.headers,
                json={
                    "author": self.person_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": full_text},
                            "shareMediaCategory": "VIDEO",
                            "media": [
                                {
                                    "status": "READY",
                                    "media": asset,
                                }
                            ],
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                },
            )
            post_id = post_resp.headers.get("x-restli-id", "")

            logger.info("linkedin_video_posted", post_id=post_id)
            return PostResult(
                platform_post_id=post_id,
                platform_post_url=f"https://www.linkedin.com/feed/update/{post_id}/",
                raw_response=post_resp.json() if post_resp.content else {},
            )

    async def get_post_metrics(self, platform_post_id: str) -> MetricsResult:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LINKEDIN_API_BASE}/organizationalEntityShareStatistics",
                headers=self.headers,
                params={"q": "organizationalEntity", "shares[0]": platform_post_id},
            )
            data = resp.json()
            stats = data.get("elements", [{}])[0].get("totalShareStatistics", {})

            return MetricsResult(
                views=stats.get("impressionCount", 0),
                likes=stats.get("likeCount", 0),
                comments=stats.get("commentCount", 0),
                shares=stats.get("shareCount", 0),
                raw_data=data,
            )

    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        from scout.config import settings

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.linkedin_client_id,
                    "client_secret": settings.linkedin_client_secret,
                },
            )
            data = resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
            }
