"""Integration tests for the pipeline flow.

These test the wiring between agents and tasks without hitting external services.
All external dependencies (Claude API, S3, Dropbox, social APIs) are mocked.
"""

import json
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPipelineWiring:
    """Test that pipeline tasks chain correctly."""

    def test_posting_adapter_factory(self):
        """Test _get_platform_adapter returns correct adapter classes."""
        from scout.tasks.posting import _get_platform_adapter

        account = MagicMock()
        account.platform_user_id = "user123"

        from scout.services.social.tiktok import TikTokPlatform
        from scout.services.social.instagram import InstagramPlatform
        from scout.services.social.youtube import YouTubePlatform
        from scout.services.social.twitter import TwitterPlatform
        from scout.services.social.linkedin import LinkedInPlatform

        assert isinstance(_get_platform_adapter("tiktok", "token", account), TikTokPlatform)
        assert isinstance(_get_platform_adapter("instagram", "token", account), InstagramPlatform)
        assert isinstance(_get_platform_adapter("youtube", "token", account), YouTubePlatform)
        assert isinstance(_get_platform_adapter("twitter", "token", account), TwitterPlatform)
        assert isinstance(_get_platform_adapter("linkedin", "token", account), LinkedInPlatform)

    def test_posting_adapter_unknown_platform_raises(self):
        from scout.tasks.posting import _get_platform_adapter

        with pytest.raises(ValueError, match="Unsupported platform"):
            _get_platform_adapter("myspace", "token", MagicMock())


class TestAgentPipelineIntegration:
    """Test that agents can be chained together with mocked Claude responses."""

    @pytest.mark.asyncio
    async def test_ingest_agent_validates_and_uploads(self):
        """IngestAgent should validate media and upload to storage."""
        from scout.agents.ingest import IngestAgent

        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_storage.upload_from_path.return_value = "s3://bucket/raw/file.mp4"

        agent = IngestAgent(mock_client, mock_storage)

        # Mock Claude response: validate then upload
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = json.dumps({
            "valid": True,
            "metadata": {"duration": 3600, "codec": "h264"},
            "s3_url": "s3://bucket/raw/file.mp4",
        })
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [text_block]
        mock_client.messages.create.return_value = response

        result = await agent.run({
            "file_path": "/tmp/podcast.mp4",
            "job_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "s3_key_prefix": "raw/user/job",
        })

        assert "result" in result
        parsed = json.loads(result["result"])
        assert parsed["valid"] is True

    @pytest.mark.asyncio
    async def test_shortform_agent_searches_transcript(self, sample_transcript):
        """ShortFormClipAgent should be able to search through transcript."""
        from scout.agents.shortform import ShortFormClipAgent

        mock_client = MagicMock()
        mock_storage = MagicMock()
        agent = ShortFormClipAgent(mock_client, mock_storage, "/tmp/work")

        # Test the search_transcript tool directly
        result = await agent.execute_tool("search_transcript", {
            "transcript": sample_transcript,
            "query": "business",
        })

        assert result["count"] == 1
        assert "starting a business" in result["matches"][0]["text"]
