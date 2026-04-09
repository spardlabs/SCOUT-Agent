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
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
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
                    "-c:v", "copy",
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
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                    "-c:a", "copy",
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
        """Burn SRT captions into a video using drawtext filter (Windows-safe)."""
        # Parse the SRT file into text segments
        captions = []
        try:
            with open(srt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                # Empty SRT - just copy the file
                subprocess.run(["ffmpeg", "-i", file_path, "-c", "copy", "-y", output_path],
                               check=True, capture_output=True)
                return output_path

            blocks = content.split("\n\n")
            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) >= 3:
                    # Parse timestamp line: "00:00:01,000 --> 00:00:05,000"
                    times = lines[1].split(" --> ")
                    if len(times) == 2:
                        text = " ".join(lines[2:]).replace("'", "\u2019").replace(":", "\\:")
                        start = MediaService._srt_to_seconds(times[0].strip())
                        end = MediaService._srt_to_seconds(times[1].strip())
                        captions.append((start, end, text))
        except Exception as e:
            logger.warning("srt_parse_failed", error=str(e))
            subprocess.run(["ffmpeg", "-i", file_path, "-c", "copy", "-y", output_path],
                           check=True, capture_output=True)
            return output_path

        if not captions:
            subprocess.run(["ffmpeg", "-i", file_path, "-c", "copy", "-y", output_path],
                           check=True, capture_output=True)
            return output_path

        # Build drawtext filter chain - one drawtext per caption segment
        drawtext_filters = []
        for start, end, text in captions:
            dt = (
                f"drawtext=text='{text}'"
                f":fontsize={font_size}"
                f":fontcolor={font_color}"
                f":borderw=3:bordercolor=black"
                f":x=(w-text_w)/2:y=h-th-60"
                f":enable='between(t,{start:.2f},{end:.2f})'"
            )
            drawtext_filters.append(dt)

        filter_chain = ",".join(drawtext_filters)

        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-vf", filter_chain,
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                    "-c:a", "copy",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("captions_burned", output=output_path, segments=len(captions))
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Caption burn failed: {e.stderr}") from e

    @staticmethod
    def _srt_to_seconds(srt_time: str) -> float:
        """Convert SRT timestamp (00:01:23,456) to seconds."""
        parts = srt_time.replace(",", ".").split(":")
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

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

    @staticmethod
    def enhance_audio(
        file_path: str,
        output_path: str,
        noise_reduction: bool = True,
        noise_floor_db: float = -40.0,
        eq_profile: str = "podcast",
        compress: bool = True,
        de_ess: bool = True,
    ) -> str:
        """Professional audio enhancement: noise reduction, EQ, compression, de-essing."""
        filters = []

        # Noise reduction (FFT-based denoiser)
        if noise_reduction:
            filters.append(f"afftdn=nf={noise_floor_db}:tn=1")

        # High-pass filter (remove rumble)
        filters.append("highpass=f=80")

        # EQ profiles
        eq_profiles = {
            "podcast": (
                "equalizer=f=120:t=q:w=1.5:g=-3,"
                "equalizer=f=3000:t=q:w=2:g=3,"
                "equalizer=f=8000:t=q:w=1.5:g=2"
            ),
            "voice": (
                "equalizer=f=200:t=q:w=1:g=-2,"
                "equalizer=f=2500:t=q:w=2:g=4,"
                "equalizer=f=6000:t=q:w=1.5:g=3"
            ),
        }
        if eq_profile in eq_profiles:
            filters.append(eq_profiles[eq_profile])

        # De-esser (sibilance reduction at 6-8kHz)
        if de_ess:
            filters.append("equalizer=f=6500:t=q:w=2:g=-3")
            filters.append("equalizer=f=8000:t=q:w=2:g=-2")

        # Dynamic range compression
        if compress:
            filters.append(
                "acompressor=threshold=-24dB:ratio=3:attack=5:release=100:makeup=2dB:knee=6dB"
            )

        # Safety limiter
        filters.append("alimiter=limit=0.95:level=1")

        filter_chain = ",".join(filters)

        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-af", filter_chain,
                    "-c:v", "copy",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("audio_enhanced", eq=eq_profile, output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Audio enhancement failed: {e.stderr}") from e

    @staticmethod
    def color_grade(
        file_path: str,
        output_path: str,
        auto_correct: bool = True,
        lut_path: str | None = None,
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
    ) -> str:
        """Apply color grading: auto correction, LUT, brightness/contrast/saturation."""
        filters = []

        # Auto color correction (clip darkest/brightest 4% per channel)
        if auto_correct:
            filters.append(
                "colorlevels=rimin=0.039:gimin=0.039:bimin=0.039:"
                "rimax=0.96:gimax=0.96:bimax=0.96"
            )

        # LUT application
        if lut_path and os.path.exists(lut_path):
            # Escape path for FFmpeg filter (Windows backslashes)
            escaped = lut_path.replace("\\", "/").replace(":", "\\:")
            filters.append(f"lut3d={escaped}")

        # Brightness, contrast, saturation
        if brightness != 0.0 or contrast != 1.0 or saturation != 1.0:
            filters.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}")

        if not filters:
            # Nothing to do, just copy
            subprocess.run(["ffmpeg", "-i", file_path, "-c", "copy", "-y", output_path],
                           check=True, capture_output=True)
            return output_path

        filter_chain = ",".join(filters)

        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-vf", filter_chain,
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                    "-c:a", "copy",
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("color_graded", auto=auto_correct, lut=bool(lut_path), output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Color grading failed: {e.stderr}") from e

    @staticmethod
    def generate_thumbnail(
        file_path: str,
        output_path: str,
        timestamp_seconds: float = 0.0,
        width: int = 1280,
        height: int = 720,
    ) -> str:
        """Extract a frame from video as a thumbnail image."""
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-ss", str(timestamp_seconds),
                    "-i", file_path,
                    "-vframes", "1",
                    "-vf", (
                        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
                    ),
                    "-y", output_path,
                ],
                check=True,
                capture_output=True,
            )
            logger.info("thumbnail_generated", output=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise MediaProcessingError(f"Thumbnail generation failed: {e.stderr}") from e
