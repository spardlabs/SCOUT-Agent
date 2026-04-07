import os

from scout.core.logging import get_logger
from scout.services.media import MediaService

logger = get_logger(__name__)


class BrandingService:
    """Apply visual branding to videos based on user profile."""

    def __init__(self, storage_service):
        self.storage = storage_service
        self.media = MediaService()

    def apply_intro_outro(
        self,
        video_path: str,
        intro_url: str | None,
        outro_url: str | None,
        work_dir: str,
    ) -> str:
        """Prepend intro and/or append outro to video."""
        parts = []

        if intro_url:
            intro_key = self.storage.key_from_url(intro_url)
            intro_path = os.path.join(work_dir, "intro.mp4")
            self.storage.download_file(intro_key, intro_path)
            parts.append(intro_path)

        parts.append(video_path)

        if outro_url:
            outro_key = self.storage.key_from_url(outro_url)
            outro_path = os.path.join(work_dir, "outro.mp4")
            self.storage.download_file(outro_key, outro_path)
            parts.append(outro_path)

        if len(parts) == 1:
            return video_path

        output_path = os.path.join(work_dir, "with_intro_outro.mp4")
        return MediaService.concat_videos(parts, output_path)

    def apply_logo(
        self,
        video_path: str,
        logo_url: str,
        work_dir: str,
        position: str = "bottom_right",
        opacity: float = 0.3,
    ) -> str:
        """Apply logo overlay to video."""
        logo_key = self.storage.key_from_url(logo_url)
        logo_path = os.path.join(work_dir, "logo.png")
        self.storage.download_file(logo_key, logo_path)

        output_path = os.path.join(work_dir, "with_logo.mp4")
        return MediaService.apply_logo_overlay(
            video_path, logo_path, output_path,
            position=position, opacity=opacity,
        )
