"""Runway AI API client for generating video intros/outros."""

import asyncio
import os
import tempfile

import httpx

from scout.config import settings
from scout.core.exceptions import MediaProcessingError
from scout.core.logging import get_logger

logger = get_logger(__name__)


class RunwayService:
    """Generate AI video clips using Runway's Gen-3 Alpha API."""

    BASE_URL = "https://api.dev.runwayml.com/v1"
    POLL_INTERVAL = 10
    MAX_POLL_TIME = 300

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.runway_api_key
        if not self.api_key:
            raise MediaProcessingError("Runway API key not configured")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": "2024-11-06",
            "Content-Type": "application/json",
        }

    async def generate_video(
        self,
        prompt: str,
        duration_seconds: int = 5,
        output_path: str = "",
    ) -> str:
        """Generate a video from a text prompt. Returns local file path."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Submit generation task
            resp = await client.post(
                f"{self.BASE_URL}/text_to_video",
                headers=self._headers(),
                json={
                    "model": "gen3a_turbo",
                    "promptText": prompt,
                    "duration": duration_seconds,
                    "ratio": "16:9",
                },
            )
            if resp.status_code != 200:
                raise MediaProcessingError(f"Runway API error: {resp.status_code} {resp.text}")

            task_id = resp.json().get("id")
            if not task_id:
                raise MediaProcessingError("Runway API did not return a task ID")

            logger.info("runway_task_submitted", task_id=task_id)

            # Poll for completion
            elapsed = 0
            while elapsed < self.MAX_POLL_TIME:
                await asyncio.sleep(self.POLL_INTERVAL)
                elapsed += self.POLL_INTERVAL

                status_resp = await client.get(
                    f"{self.BASE_URL}/tasks/{task_id}",
                    headers=self._headers(),
                )
                task_data = status_resp.json()
                status = task_data.get("status", "")

                if status == "SUCCEEDED":
                    output_url = task_data.get("output", [None])[0]
                    if not output_url:
                        raise MediaProcessingError("Runway task succeeded but no output URL")

                    # Download the video
                    if not output_path:
                        output_path = os.path.join(tempfile.gettempdir(), f"runway_{task_id}.mp4")

                    video_resp = await client.get(output_url)
                    with open(output_path, "wb") as f:
                        f.write(video_resp.content)

                    logger.info("runway_video_downloaded", path=output_path)
                    return output_path

                elif status == "FAILED":
                    error = task_data.get("failure", "Unknown error")
                    raise MediaProcessingError(f"Runway generation failed: {error}")

                logger.info("runway_polling", task_id=task_id, status=status, elapsed=elapsed)

            raise MediaProcessingError(f"Runway task timed out after {self.MAX_POLL_TIME}s")

    async def generate_intro(
        self,
        brand_name: str,
        brand_colors: dict,
        style: str = "cinematic",
        output_path: str = "",
    ) -> str:
        """Generate a branded intro video."""
        prompt = (
            f"A {style} video intro for '{brand_name}'. "
            f"Brand colors: primary {brand_colors.get('primary', '#1a1a2e')}, "
            f"accent {brand_colors.get('secondary', '#e94560')}. "
            f"Smooth motion graphics, professional broadcast quality, "
            f"elegant logo reveal animation. 5 seconds."
        )
        return await self.generate_video(prompt, duration_seconds=5, output_path=output_path)

    async def generate_outro(
        self,
        brand_name: str,
        brand_colors: dict,
        call_to_action: str = "Subscribe for more",
        style: str = "cinematic",
        output_path: str = "",
    ) -> str:
        """Generate a branded outro video."""
        prompt = (
            f"A {style} video outro for '{brand_name}'. "
            f"Text: '{call_to_action}'. "
            f"Brand colors: primary {brand_colors.get('primary', '#1a1a2e')}, "
            f"accent {brand_colors.get('secondary', '#e94560')}. "
            f"Professional broadcast quality, smooth fade-out. 5 seconds."
        )
        return await self.generate_video(prompt, duration_seconds=5, output_path=output_path)
