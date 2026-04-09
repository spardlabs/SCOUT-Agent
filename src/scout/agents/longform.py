import json
import os
from typing import Any

import anthropic

from scout.agents.base import BaseAgent
from scout.agents.tools.media import MEDIA_TOOLS
from scout.agents.tools.storage import STORAGE_TOOLS
from scout.agents.tools.transcript import TRANSCRIPT_TOOLS
from scout.core.logging import get_logger
from scout.services.branding import BrandingService
from scout.services.media import MediaService
from scout.services.storage import StorageService
from scout.services.transcription import TranscriptionService

logger = get_logger(__name__)


class LongFormEditAgent(BaseAgent):
    """Agent responsible for editing full-length podcast episodes.

    Takes a raw podcast video and the user's editing profile, then:
    - Transcribes the audio
    - Removes silences based on profile preferences
    - Normalizes audio levels
    - Applies branding (intro, outro, logo)
    - Renders the final edited episode
    """

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        storage: StorageService,
        work_dir: str,
    ):
        super().__init__(anthropic_client)
        self.storage = storage
        self.media = MediaService()
        self.transcription = TranscriptionService()
        self.branding = BrandingService(storage)
        self.work_dir = work_dir

    def get_system_prompt(self) -> str:
        return """You are the Long-Form Editing Agent for SCOUT, a podcast post-production pipeline.

Your job is to edit a raw podcast video based on the user's editing profile preferences.

You will receive:
- file_path: path to the raw video file
- profile: the user's editing preferences

Follow these steps:
1. Transcribe the audio using transcribe_audio
2. Detect silences using the profile's silence_threshold_ms
3. Remove detected silences from the video
4. Normalize audio to the profile's target_lufs
5. Apply branding if configured (intro, outro, logo)

Interpret the editing_style preference:
- "tight": Use aggressive silence removal (threshold -25dB), faster pacing
- "conversational": Moderate silence removal (threshold -30dB), natural pacing
- "cinematic": Minimal silence removal (threshold -35dB), preserve dramatic pauses

Return a JSON result with:
- edited_file_path: path to the final edited video
- transcript: the full transcript data
- edit_summary: description of edits made
- original_duration: duration before editing
- edited_duration: duration after editing
"""

    def get_tools(self) -> list[dict]:
        return [
            *MEDIA_TOOLS,
            next(t for t in TRANSCRIPT_TOOLS if t["name"] == "transcribe_audio"),
            next(t for t in TRANSCRIPT_TOOLS if t["name"] == "generate_srt"),
            *STORAGE_TOOLS,
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "get_media_info":
            return self.media.get_media_info(tool_input["file_path"])

        elif tool_name == "detect_silences":
            return self.media.detect_silences(
                tool_input["file_path"],
                threshold_db=tool_input.get("threshold_db", -30.0),
                min_duration_ms=tool_input.get("min_duration_ms", 1500),
            )

        elif tool_name == "remove_segments":
            return self.media.remove_segments(
                tool_input["file_path"],
                tool_input["segments"],
                tool_input["output_path"],
            )

        elif tool_name == "normalize_audio":
            return self.media.normalize_audio(
                tool_input["file_path"],
                target_lufs=tool_input.get("target_lufs", -16.0),
                output_path=tool_input.get("output_path", ""),
            )

        elif tool_name == "transcribe_audio":
            transcript = self.transcription.transcribe(tool_input["file_path"])
            # Save transcript to work dir
            transcript_path = os.path.join(self.work_dir, "transcript.json")
            self.transcription.save_transcript(transcript, transcript_path)
            return transcript

        elif tool_name == "generate_srt":
            return self.transcription.transcript_to_srt(
                tool_input["transcript"],
                tool_input["output_path"],
            )

        elif tool_name == "apply_logo_overlay":
            return self.media.apply_logo_overlay(
                tool_input["file_path"],
                tool_input["logo_path"],
                tool_input["output_path"],
                position=tool_input.get("position", "bottom_right"),
                opacity=tool_input.get("opacity", 0.3),
            )

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
