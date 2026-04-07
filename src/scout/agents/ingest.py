import os
import tempfile
from typing import Any

import anthropic

from scout.agents.base import BaseAgent
from scout.agents.tools.storage import STORAGE_TOOLS
from scout.agents.tools.media import MEDIA_TOOLS
from scout.core.logging import get_logger
from scout.services.media import MediaService
from scout.services.storage import StorageService

logger = get_logger(__name__)


class IngestAgent(BaseAgent):
    """Agent responsible for ingesting raw podcast uploads.

    Validates media files, extracts metadata, uploads to S3,
    and creates job records for downstream processing.
    """

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        storage: StorageService,
    ):
        super().__init__(anthropic_client)
        self.storage = storage
        self.media = MediaService()

    def get_system_prompt(self) -> str:
        return """You are the Ingest Agent for SCOUT, a podcast post-production pipeline.

Your job is to validate and ingest raw podcast video files uploaded by users.

For each file:
1. Use get_media_info to inspect the file metadata
2. Validate it's a video file (must have video and audio streams)
3. Validate duration is at least 60 seconds (podcasts should be substantial)
4. Upload the validated file to S3 storage

Return a JSON result with:
- valid: boolean
- metadata: {duration, codec, resolution, bitrate, file_size}
- s3_url: the uploaded file URL (if valid)
- rejection_reason: string (if invalid)
"""

    def get_tools(self) -> list[dict]:
        # Only need media info and storage tools
        return [
            next(t for t in MEDIA_TOOLS if t["name"] == "get_media_info"),
            *STORAGE_TOOLS,
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "get_media_info":
            return self.media.get_media_info(tool_input["file_path"])

        elif tool_name == "upload_to_storage":
            return self.storage.upload_from_path(
                tool_input["local_path"],
                tool_input["s3_key"],
                tool_input.get("content_type", "video/mp4"),
            )

        elif tool_name == "download_from_storage":
            return self.storage.download_file(
                tool_input["s3_key"],
                tool_input["local_path"],
            )

        raise ValueError(f"Unknown tool: {tool_name}")
