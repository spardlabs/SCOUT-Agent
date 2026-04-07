"""Tests for the media processing service."""

import json
from unittest.mock import patch, MagicMock

from scout.services.media import MediaService


class TestMediaService:
    def test_get_media_info_parses_ffprobe_output(self):
        mock_output = json.dumps({
            "format": {"duration": "3600.0", "bit_rate": "5000000"},
            "streams": [{"codec_type": "video"}, {"codec_type": "audio"}],
        })
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = MediaService.get_media_info("/fake/path.mp4")
            assert result["format"]["duration"] == "3600.0"
            assert len(result["streams"]) == 2

    def test_detect_silences_parses_ffmpeg_output(self):
        stderr_output = (
            "[silencedetect @ 0x123] silence_start: 10.5\n"
            "[silencedetect @ 0x123] silence_end: 12.3 | silence_duration: 1.8\n"
            "[silencedetect @ 0x123] silence_start: 45.0\n"
            "[silencedetect @ 0x123] silence_end: 48.5 | silence_duration: 3.5\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stderr=stderr_output, returncode=0)
            result = MediaService.detect_silences("/fake/path.mp4")
            assert len(result) == 2
            assert result[0] == {"start": 10.5, "end": 12.3}
            assert result[1] == {"start": 45.0, "end": 48.5}

    def test_srt_time_formatting(self):
        from scout.services.transcription import TranscriptionService

        assert TranscriptionService._format_srt_time(0.0) == "00:00:00,000"
        assert TranscriptionService._format_srt_time(61.5) == "00:01:01,500"
        assert TranscriptionService._format_srt_time(3661.123) == "01:01:01,123"
