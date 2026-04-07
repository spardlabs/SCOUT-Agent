import json
import os
from typing import Any

import anthropic

from scout.agents.base import BaseAgent
from scout.agents.tools.media import MEDIA_TOOLS
from scout.agents.tools.storage import STORAGE_TOOLS
from scout.agents.tools.transcript import TRANSCRIPT_TOOLS
from scout.core.logging import get_logger
from scout.services.media import MediaService
from scout.services.storage import StorageService
from scout.services.transcription import TranscriptionService

logger = get_logger(__name__)


class ShortFormClipAgent(BaseAgent):
    """Agent responsible for generating short-form clips from edited podcasts.

    Analyzes the transcript to identify viral-worthy segments, then:
    - Selects the best clips based on user preferences
    - Extracts each clip from the source video
    - Adds captions with word-level timestamps
    - Creates platform-specific variants (9:16, 1:1, etc.)
    - Generates thumbnails
    """

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        storage: StorageService,
        work_dir: str,
    ):
        super().__init__(anthropic_client, max_turns=30)
        self.storage = storage
        self.media = MediaService()
        self.transcription = TranscriptionService()
        self.work_dir = work_dir

    def get_system_prompt(self) -> str:
        return """You are the Short-Form Clip Agent for SCOUT, a podcast post-production pipeline.

Your job is to identify the best short-form clips from a podcast episode and prepare them for social media.

You will receive:
- video_path: path to the edited podcast video
- transcript: the full transcript with word-level timestamps
- profile: user's editing preferences (topics, virality_preferences, clip_length_range, target_platforms, caption_style)

Follow these steps:

1. ANALYZE the transcript to identify the best clip candidates. Look for:
   - Viral moments: surprising statements, hot takes, controversial opinions
   - Key insights: valuable advice, unique perspectives, expert knowledge
   - Emotional peaks: humor, passion, storytelling climaxes
   - Strong hooks: segments that start with attention-grabbing statements

2. SCORE each candidate clip (0.0 to 1.0) based on the user's virality_preferences:
   - humor: weight funny moments
   - controversy: weight provocative takes
   - education: weight informative content

3. SELECT the top 5 clips within the user's clip_length_range (default 30-90 seconds)

4. For each selected clip:
   a. Extract the clip using extract_clip
   b. Generate an SRT file from the transcript words in that time range
   c. Burn captions into the clip
   d. Convert to 9:16 aspect ratio for vertical platforms (TikTok, Reels, Shorts)
   e. Upload all variants to storage

5. Return a JSON result with an array of clips, each containing:
   - title: catchy title for the clip
   - description: engaging caption/hook text for social media
   - start_time_seconds, end_time_seconds
   - virality_score: your assessment
   - topics: relevant topics from the content
   - transcript_text: the text of the clip
   - clip_file_url: S3 URL of the master clip
   - platform_variants: {tiktok: url, instagram: url, youtube: url}

Be creative with titles and descriptions - they should be scroll-stopping hooks.
"""

    def get_tools(self) -> list[dict]:
        return [*MEDIA_TOOLS, *TRANSCRIPT_TOOLS, *STORAGE_TOOLS]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "get_media_info":
            return self.media.get_media_info(tool_input["file_path"])

        elif tool_name == "extract_clip":
            return self.media.extract_clip(
                tool_input["file_path"],
                tool_input["start_seconds"],
                tool_input["end_seconds"],
                tool_input["output_path"],
            )

        elif tool_name == "convert_aspect_ratio":
            return self.media.convert_aspect_ratio(
                tool_input["file_path"],
                tool_input["output_path"],
                width=tool_input.get("width", 1080),
                height=tool_input.get("height", 1920),
            )

        elif tool_name == "burn_captions":
            return self.media.burn_captions(
                tool_input["file_path"],
                tool_input["srt_path"],
                tool_input["output_path"],
                font_size=tool_input.get("font_size", 48),
            )

        elif tool_name == "generate_srt":
            return self.transcription.transcript_to_srt(
                tool_input["transcript"],
                tool_input["output_path"],
            )

        elif tool_name == "search_transcript":
            # Simple keyword search in transcript
            query = tool_input["query"].lower()
            transcript = tool_input["transcript"]
            matches = []
            for seg in transcript.get("segments", []):
                if query in seg["text"].lower():
                    matches.append(seg)
            return {"query": query, "matches": matches, "count": len(matches)}

        elif tool_name == "transcribe_audio":
            return self.transcription.transcribe(tool_input["file_path"])

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
