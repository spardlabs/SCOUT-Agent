"""Background pipeline processor.

Runs the full podcast processing pipeline as async background tasks
inside FastAPI - no Celery worker needed.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Any

import anthropic

from scout.config import settings
from scout.core.logging import get_logger
from scout.db.session import async_session_factory
from scout.db.models.job import Job, JobStatus
from scout.db.models.clip import Clip, ClipStatus
from scout.db.models.profile import EditingProfile

logger = get_logger(__name__)


async def _update_job_status(job_id: str, status: JobStatus, **kwargs):
    """Update a job's status in the database."""
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            for key, value in kwargs.items():
                setattr(job, key, value)
            await db.commit()
            logger.info("job_status_updated", job_id=job_id, status=status.value)


async def _get_profile(user_id: str) -> dict:
    """Load user's editing profile."""
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(
            select(EditingProfile).where(EditingProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return {}
        return {
            "silence_threshold_ms": profile.silence_threshold_ms,
            "target_lufs": profile.target_lufs,
            "editing_style": profile.editing_style,
            "topics": profile.topics,
            "virality_preferences": profile.virality_preferences,
            "target_platforms": profile.target_platforms,
            "clip_length_range": profile.clip_length_range,
            "caption_style": profile.caption_style,
        }


def _has_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _get_media_duration(file_path: str) -> float | None:
    """Get media duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", file_path,
            ],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except Exception:
        return None


def _transcribe_audio(file_path: str) -> dict | None:
    """Transcribe audio using faster-whisper if available."""
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(file_path, word_timestamps=True, vad_filter=True)

        transcript = {
            "language": info.language,
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
                    })
            transcript["segments"].append(seg_data)

        return transcript
    except ImportError:
        logger.warning("faster_whisper_not_available")
        return None
    except Exception as e:
        logger.error("transcription_failed", error=str(e))
        return None


async def _run_clip_analysis(
    client: anthropic.Anthropic,
    transcript: dict,
    profile: dict,
) -> list[dict]:
    """Use Claude to analyze transcript and identify best clips."""
    transcript_text = " ".join(seg["text"] for seg in transcript.get("segments", []))

    if not transcript_text.strip():
        return []

    # Truncate if too long for the API
    if len(transcript_text) > 30000:
        transcript_text = transcript_text[:30000] + "..."

    topics = profile.get("topics", [])
    virality = profile.get("virality_preferences", {})
    clip_range = profile.get("clip_length_range", {"min_seconds": 30, "max_seconds": 90})

    prompt = f"""Analyze this podcast transcript and identify the 3-5 best clips for social media.

TRANSCRIPT:
{transcript_text}

USER PREFERENCES:
- Topics of interest: {', '.join(topics) if topics else 'general'}
- Virality preferences: humor={virality.get('humor', 0.5)}, education={virality.get('education', 0.7)}, controversy={virality.get('controversy', 0.2)}
- Clip length: {clip_range.get('min_seconds', 30)}-{clip_range.get('max_seconds', 90)} seconds

For each clip, return a JSON array with objects containing:
- "title": catchy title (scroll-stopping hook)
- "description": engaging caption for social media
- "start_time_seconds": approximate start time in the transcript
- "end_time_seconds": approximate end time
- "virality_score": your assessment 0.0-1.0
- "topics": relevant topic tags
- "transcript_text": the text of the clip segment

Return ONLY the JSON array, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        clips = json.loads(text)
        if isinstance(clips, dict):
            clips = clips.get("clips", [])
        return clips
    except Exception as e:
        logger.error("clip_analysis_failed", error=str(e))
        return []


async def process_episode(job_id: str, user_id: str, file_path: str):
    """Full pipeline: ingest -> transcribe -> analyze -> generate clips.

    Runs as a background task. Updates job status at each stage.
    """
    logger.info("pipeline_started", job_id=job_id)

    # Wait for the upload transaction to be fully committed
    await asyncio.sleep(2)

    try:
        # ── Stage 1: Ingest ──────────────────────────────────────────
        await _update_job_status(job_id, JobStatus.INGESTING, started_at=datetime.utcnow())

        duration = _get_media_duration(file_path) if _has_ffmpeg() else None
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        await _update_job_status(
            job_id, JobStatus.INGESTED,
            duration_seconds=duration,
            file_metadata={"file_size": file_size, "has_ffmpeg": _has_ffmpeg()},
        )
        logger.info("ingest_complete", job_id=job_id, duration=duration)

        # ── Stage 2: Transcribe ──────────────────────────────────────
        await _update_job_status(job_id, JobStatus.EDITING)

        transcript = None
        transcript_text = ""

        # Try faster-whisper transcription
        transcript = await asyncio.to_thread(_transcribe_audio, file_path)

        if transcript:
            transcript_text = " ".join(seg["text"] for seg in transcript.get("segments", []))
            # Save transcript
            transcript_path = file_path.rsplit(".", 1)[0] + "_transcript.json"
            with open(transcript_path, "w") as f:
                json.dump(transcript, f, indent=2)
            await _update_job_status(job_id, JobStatus.EDITED, transcript_url=transcript_path)
            logger.info("transcription_complete", job_id=job_id, segments=len(transcript["segments"]))
        else:
            # No whisper available - mark as edited anyway and proceed
            await _update_job_status(job_id, JobStatus.EDITED)
            logger.warning("transcription_skipped", job_id=job_id)

        # ── Stage 3: Generate Clips (AI Analysis) ───────────────────
        await _update_job_status(job_id, JobStatus.CLIPPING)

        profile = await _get_profile(user_id)

        if not settings.anthropic_api_key:
            logger.warning("no_anthropic_key", job_id=job_id)
            await _update_job_status(
                job_id, JobStatus.FAILED,
                error_message="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
            )
            return

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        clips_data = []
        if transcript and transcript_text.strip():
            clips_data = await _run_clip_analysis(client, transcript, profile)
            logger.info("clip_analysis_complete", job_id=job_id, clips=len(clips_data))
        else:
            # No transcript - ask Claude to generate placeholder clips based on filename/duration
            logger.info("generating_placeholder_clips", job_id=job_id)
            clips_data = [
                {
                    "title": "Episode Highlight",
                    "description": "Check out this moment from our latest episode!",
                    "start_time_seconds": 0,
                    "end_time_seconds": min(60, duration or 60),
                    "virality_score": 0.7,
                    "topics": profile.get("topics", ["podcast"]),
                    "transcript_text": "(Transcription unavailable - install faster-whisper for full analysis)",
                }
            ]

        # Save clips to database
        async with async_session_factory() as db:
            for clip_data in clips_data:
                clip = Clip(
                    job_id=job_id,
                    user_id=user_id,
                    title=clip_data.get("title", "Untitled Clip"),
                    description=clip_data.get("description", ""),
                    start_time_seconds=clip_data.get("start_time_seconds", 0),
                    end_time_seconds=clip_data.get("end_time_seconds", 60),
                    duration_seconds=(
                        clip_data.get("end_time_seconds", 60)
                        - clip_data.get("start_time_seconds", 0)
                    ),
                    clip_file_url=file_path,  # Would be extracted clip in production
                    virality_score=clip_data.get("virality_score", 0.5),
                    topics=clip_data.get("topics", []),
                    transcript_text=clip_data.get("transcript_text", ""),
                    status=ClipStatus.GENERATED,
                )
                db.add(clip)
            await db.commit()

        await _update_job_status(job_id, JobStatus.CLIPPED)

        # ── Stage 4: Schedule (mark complete) ────────────────────────
        await _update_job_status(job_id, JobStatus.SCHEDULING)
        # In production, SchedulerAgent would create Post records here
        await asyncio.sleep(1)

        await _update_job_status(
            job_id, JobStatus.COMPLETE,
            completed_at=datetime.utcnow(),
        )
        logger.info("pipeline_complete", job_id=job_id, clips_generated=len(clips_data))

    except Exception as e:
        logger.error("pipeline_failed", job_id=job_id, error=str(e))
        await _update_job_status(
            job_id, JobStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.utcnow(),
        )
