"""Tests for transcription service."""

import json
import os
import tempfile

from scout.services.transcription import TranscriptionService


class TestTranscriptionService:
    def test_transcript_to_text(self, sample_transcript):
        text = TranscriptionService.transcript_to_text(sample_transcript)
        assert "Welcome to the show" in text
        assert "AI can now write code" in text
        assert "starting a business" in text

    def test_transcript_to_srt(self, sample_transcript):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False) as f:
            srt_path = f.name

        try:
            TranscriptionService.transcript_to_srt(sample_transcript, srt_path)
            with open(srt_path) as f:
                content = f.read()
            # SRT format: counter, timestamp, text, blank line
            assert "1\n" in content
            assert "00:00:00,000 --> 00:00:15,000" in content
            assert "Welcome to the show" in content
        finally:
            os.unlink(srt_path)

    def test_save_transcript(self, sample_transcript):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "transcript.json")
            TranscriptionService.save_transcript(sample_transcript, path)

            assert os.path.exists(path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["language"] == "en"
            assert len(loaded["segments"]) == 3

    def test_format_srt_time_edge_cases(self):
        assert TranscriptionService._format_srt_time(0) == "00:00:00,000"
        assert TranscriptionService._format_srt_time(0.001) == "00:00:00,001"
        assert TranscriptionService._format_srt_time(59.999) == "00:00:59,999"
        assert TranscriptionService._format_srt_time(3600) == "01:00:00,000"
        assert TranscriptionService._format_srt_time(7261.5) == "02:01:01,500"
