import json
import os
import tempfile

from scout.core.exceptions import MediaProcessingError
from scout.core.logging import get_logger

logger = get_logger(__name__)


class TranscriptionService:
    """Whisper-based audio transcription with word-level timestamps."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )
        return self._model

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio/video file and return structured transcript."""
        try:
            model = self._get_model()
            segments, info = model.transcribe(
                audio_path,
                word_timestamps=True,
                vad_filter=True,
            )

            transcript = {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": [],
            }

            for segment in segments:
                seg_data = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": [],
                }
                if segment.words:
                    for word in segment.words:
                        seg_data["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability,
                        })
                transcript["segments"].append(seg_data)

            logger.info(
                "transcription_complete",
                language=info.language,
                duration=info.duration,
                segments=len(transcript["segments"]),
            )
            return transcript

        except Exception as e:
            raise MediaProcessingError(f"Transcription failed: {e}") from e

    @staticmethod
    def transcript_to_srt(transcript: dict, output_path: str) -> str:
        """Convert transcript to SRT subtitle format."""
        with open(output_path, "w") as f:
            counter = 1
            for segment in transcript["segments"]:
                start = TranscriptionService._format_srt_time(segment["start"])
                end = TranscriptionService._format_srt_time(segment["end"])
                f.write(f"{counter}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{segment['text']}\n\n")
                counter += 1
        return output_path

    @staticmethod
    def transcript_to_text(transcript: dict) -> str:
        """Extract plain text from transcript."""
        return " ".join(seg["text"] for seg in transcript["segments"])

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def save_transcript(transcript: dict, output_path: str) -> str:
        """Save transcript as JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(transcript, f, indent=2)
        return output_path
