"""Tests for IngestAgent tool dispatch."""

import json
from unittest.mock import MagicMock, patch

import pytest

from scout.agents.ingest import IngestAgent


class TestIngestAgent:
    def _make_agent(self):
        mock_client = MagicMock()
        mock_storage = MagicMock()
        return IngestAgent(mock_client, mock_storage)

    def test_system_prompt_mentions_validation(self):
        agent = self._make_agent()
        prompt = agent.get_system_prompt()
        assert "validate" in prompt.lower() or "valid" in prompt.lower()

    def test_tools_include_media_info(self):
        agent = self._make_agent()
        tool_names = [t["name"] for t in agent.get_tools()]
        assert "get_media_info" in tool_names
        assert "upload_to_storage" in tool_names

    @pytest.mark.asyncio
    async def test_execute_get_media_info(self):
        agent = self._make_agent()
        with patch.object(agent.media, "get_media_info", return_value={"format": {"duration": "120"}}) as mock:
            result = await agent.execute_tool("get_media_info", {"file_path": "/tmp/test.mp4"})
            mock.assert_called_once_with("/tmp/test.mp4")
            assert result["format"]["duration"] == "120"

    @pytest.mark.asyncio
    async def test_execute_upload_to_storage(self):
        agent = self._make_agent()
        agent.storage.upload_from_path = MagicMock(return_value="s3://bucket/key")
        result = await agent.execute_tool("upload_to_storage", {
            "local_path": "/tmp/test.mp4",
            "s3_key": "raw/user/job/test.mp4",
        })
        assert result == "s3://bucket/key"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_raises(self):
        agent = self._make_agent()
        with pytest.raises(ValueError, match="Unknown tool"):
            await agent.execute_tool("nonexistent_tool", {})
