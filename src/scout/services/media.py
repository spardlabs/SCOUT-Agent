import json
import os
import subprocess
import tempfile

from scout.core.exceptions import MediaProcessingError
from scout.core.logging import get_logger

logger = get_logger(__name__)


class MediaService:
    """FFmpeg-based media processing service."""

    @staticmethod
    def get_media_info(file_path: str) -> dict:
        """Extract media metadata using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    file_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"ffprobe failed: {e.stderr}") from e

    @staticmethod
    def detect_silences(
        file_path: str,
        threshold_db: float = -30.0,
        min_duration_ms: int = 1500,
    ) -> list[dict]:
        """Detect silent segments in audio/video."""
        min_duration_s = min_duration_ms / 1000.0
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", file_path,
                    "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration_s}",
                    "-f", "null",
                    "-",
                ],
                capture_output=True,
                text=True,
            )
            # Parse silence detect output from stderr
            silences = []
            lines = result.stderr.split("\n")
            current_start = None
            for line in lines:
                if "silence_start:" in line:
                    current_start = float(line.split("silence_start:")[1].strip().split()[0])
                elif "silence_end:" in line and current_start is not None:
                    parts = line.split("silence_end:")[1].strip().split("|")
                    end = float(parts[0].strip())
                    silences.append({"start": current_start, "end": end})
                    current_start = None

            logger.info("silences_detected", count=len(silences), file=file_path)
            return silences
        except Exception as e:
            raise MediaProcessingError(f"Silence detection failed: {e}") from e

    @staticmethod
    def remove_segments(
        file_path: str,
        segments: list[dict],
        output_path: str,
    ) -> str:
        """Remove time segments from a video file."""
        if not segments:
            # No segments to remove, just copy
            subprocess.run(
                ["ffmpeg", "-i", file_path, "-c", "copy", output_path],
                check=True,
                capture_output=True,
            )
            return output_path

        # Build a complex filter to select non-silent segments
        info = MediaService.get_media_info(file_path)
        duration = float(info["format"]["duration"])

        # Calculate keep segments (inverse of remove segments)
        keep_segments = []
        prev_end = 0.0
        for seg in sorted(segments, key=lambda s: s["start"]):
            if seg["start"] > prev_end:
                keep_segments.append({"start": prev_end, "end": seg["start"]})
            prev_end = seg["end"]
        if prev_end < duration:
            keep_segments.append({"start": prev_end, "end": duration})

        if not keep_segments:
            raise MediaProcessingError("No content remaining after removing segments")

        # Use concat filter with trim
        filter_parts = []
        for i, seg in enumerate(keep_segments):
            filter_parts.append(
                f"[0:v]trim=start={seg['start']}:end={seg['end']},setpts=PTS-STARTPTS[v{i}];"
                f"[0:a]atrim=start={seg['start']}:end={seg['end']},asetpts=PTS-STARTPTS[a{i}];"
            )

        n = len(keep_segments)
        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(n))
        filter_complex = "".join(filter_parts) + f"{concat_inputs}concat=n={n}:v=1:a=1[outv][outa]"

        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-filter_complex", filter_complex,
                    "-map", "[outv]", "-map", "[outa]",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("segments_removed", count=len(segments), output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Segment removal failed: {e.stderr}") from e

    @staticmethod
    def normalize_audio(file_path: str, target_lufs: float = -16.0, output_path: str = "") -> str:
        """Normalize audio to target LUFS level."""
        if not output_path:
            base, ext = os.path.splitext(file_path)
            output_path = f"{base}_normalized{ext}"

        try:
            # Two-pass loudness normalization
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-",
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("audio_normalized", target_lufs=target_lufs, output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Audio normalization failed: {e.stderr}") from e

    @staticmethod
    def concat_videos(file_paths: list[str], output_path: str) -> str:
        """Concatenate multiple video files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for path in file_paths:
                f.write(f"file '{path}'\n")
            list_file = f.name

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c", "copy",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("videos_concatenated", count=len(file_paths), output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Video concat failed: {e.stderr}") from e
        finally:
            os.unlink(list_file)

    @staticmethod
    def extract_clip(
        file_path: str,
        start_seconds: float,
        end_seconds: float,
        output_path: str,
    ) -> str:
        """Extract a clip from a video file."""
        duration = end_seconds - start_seconds
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-ss", str(start_seconds),
                    "-i", file_path,
                    "-t", str(duration),
                    "-c", "copy",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info(
                "clip_extracted",
                start=start_seconds,
                end=end_seconds,
                output=output_path,
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Clip extraction failed: {e.stderr}") from e

    @staticmethod
    def convert_aspect_ratio(
        file_path: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
    ) -> str:
        """Convert video to a specific aspect ratio (e.g., 9:16 for TikTok/Reels)."""
        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-vf", (
                        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
                    ),
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("aspect_ratio_converted", output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Aspect ratio conversion failed: {e.stderr}") from e

    @staticmethod
    def burn_captions(
        file_path: str,
        srt_path: str,
        output_path: str,
        font_size: int = 48,
        font_color: str = "white",
    ) -> str:
        """Burn SRT captions into a video."""
        style = f"FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-vf", f"subtitles={srt_path}:force_style='{style}'",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("captions_burned", output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Caption burn failed: {e.stderr}") from e

    @staticmethod
    def apply_logo_overlay(
        file_path: str,
        logo_path: str,
        output_path: str,
        position: str = "bottom_right",
        opacity: float = 0.3,
        scale: float = 0.1,
    ) -> str:
        """Overlay a logo onto a video."""
        # Position mappings
        positions = {
            "top_left": "10:10",
            "top_right": "W-w-10:10",
            "bottom_left": "10:H-h-10",
            "bottom_right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2",
        }
        pos = positions.get(position, positions["bottom_right"])

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", file_path,
                    "-i", logo_path,
                    "-filter_complex", (
                        f"[1:v]scale=iw*{scale}:-1,format=rgba,"
                        f"colorchannelmixer=aa={opacity}[logo];"
                        f"[0:v][logo]overlay={pos}[out]"
                    ),
                    "-map", "[out]", "-map", "0:a",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("logo_applied", position=position, output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Logo overlay failed: {e.stderr}") from e
