"""Tests for ShortFormClipAgent tool dispatch."""

import json
from unittest.mock import MagicMock, patch

import pytest

from scout.agents.shortform import ShortFormClipAgent


class TestShortFormClipAgent:
    def _make_agent(self):
        mock_client = MagicMock()
        mock_storage = MagicMock()
        return ShortFormClipAgent(mock_client, mock_storage, "/tmp/work")

    def test_system_prompt_mentions_clips(self):
        agent = self._make_agent()
        prompt = agent.get_system_prompt()
        assert "clip" in prompt.lower()
        assert "viral" in prompt.lower()

    def test_tools_include_clip_tools(self):
        agent = self._make_agent()
        tool_names = [t["name"] for t in agent.get_tools()]
        assert "extract_clip" in tool_names
        assert "burn_captions" in tool_names
        assert "convert_aspect_ratio" in tool_names
        assert "search_transcript" in tool_names

    @pytest.mark.asyncio
    async def test_execute_search_transcript(self, sample_transcript):
        agent = self._make_agent()
        result = await agent.execute_tool("search_transcript", {
            "transcript": sample_transcript,
            "query": "AI",
        })
        assert result["count"] > 0
        assert result["query"] == "ai"

    @pytest.mark.asyncio
    async def test_search_transcript_no_matches(self, sample_transcript):
        agent = self._make_agent()
        result = await agent.execute_tool("search_transcript", {
            "transcript": sample_transcript,
            "query": "quantum computing",
        })
        assert result["count"] == 0
        assert result["matches"] == []

    @pytest.mark.asyncio
    async def test_execute_extract_clip(self):
        agent = self._make_agent()
        with patch.object(agent.media, "extract_clip", return_value="/tmp/clip.mp4"):
            result = await agent.execute_tool("extract_clip", {
                "file_path": "/tmp/video.mp4",
                "start_seconds": 120.0,
                "end_seconds": 180.0,
                "output_path": "/tmp/clip.mp4",
            })
            assert result == "/tmp/clip.mp4"

    @pytest.mark.asyncio
    async def test_max_turns_higher_for_complex_agent(self):
        agent = self._make_agent()
        assert agent.max_turns == 30  # Higher than default 20
