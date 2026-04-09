"""Background pipeline processor - Professional Edition.

Runs the full podcast processing pipeline as async background tasks:
1. Ingest (metadata extraction)
2. Audio Enhancement (noise reduction, EQ, compression, de-essing, normalization)
3. Color Grading (auto correction, LUT, brightness/contrast/saturation)
4. Editing (transcription, silence detection & removal)
5. Branding (intro/outro via Runway AI or static assets, logo overlay)
6. AI Clip Analysis (Claude identifies viral clips from transcript)
7. Render Clips (extract, caption, platform variants, thumbnails)
8. Complete
"""

import asyncio
import json
import os
import tempfile
import uuid as uuid_mod
from datetime import datetime

import anthropic

from scout.config import settings
from scout.core.logging import get_logger
from scout.db.session import async_session_factory
from scout.db.models.job import Job, JobStatus
from scout.db.models.clip import Clip, ClipStatus
from scout.db.models.profile import EditingProfile
from scout.services.media import MediaService
from scout.services.transcription import TranscriptionService

logger = get_logger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _update_job(job_id: str, **kwargs):
    """Update job fields in the database."""
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(select(Job).where(Job.id == uuid_mod.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job:
            for key, value in kwargs.items():
                setattr(job, key, value)
            await db.commit()
            status = kwargs.get("status")
            if status:
                logger.info("job_status", job_id=job_id, status=status.value if hasattr(status, "value") else status)


async def _get_profile(user_id: str) -> dict:
    """Load user's editing profile."""
    from sqlalchemy import select

    async with async_session_factory() as db:
        result = await db.execute(select(EditingProfile).where(EditingProfile.user_id == uuid_mod.UUID(user_id)))
        profile = result.scalar_one_or_none()
        if not profile:
            return {}
        return {
            "silence_threshold_ms": profile.silence_threshold_ms,
            "silence_action": profile.silence_action,
            "target_lufs": profile.target_lufs,
            "editing_style": profile.editing_style,
            "topics": profile.topics,
            "virality_preferences": profile.virality_preferences,
            "target_platforms": profile.target_platforms,
            "clip_length_range": profile.clip_length_range,
            "caption_style": profile.caption_style,
            "brand_color_primary": profile.brand_color_primary,
            "brand_color_secondary": profile.brand_color_secondary,
            "intro_asset_url": profile.intro_asset_url,
            "outro_asset_url": profile.outro_asset_url,
            "logo_asset_url": profile.logo_asset_url,
        }


def _has_ffmpeg() -> bool:
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ── Pipeline ─────────────────────────────────────────────────────────────────

async def process_episode(job_id: str, user_id: str, file_path: str):
    """Full professional editing pipeline."""
    logger.info("pipeline_start", job_id=job_id)

    # Wait for upload transaction to commit
    await asyncio.sleep(2)

    if not os.path.exists(file_path):
        await _update_job(job_id, status=JobStatus.FAILED, error_message="File not found")
        return

    work_dir = os.path.dirname(file_path)
    current_file = file_path
    profile = await _get_profile(user_id)
    has_ffmpeg = _has_ffmpeg()

    try:
        # ── Stage 1: Ingest ──────────────────────────────────────────
        await _update_job(job_id, status=JobStatus.INGESTING, started_at=datetime.utcnow())

        duration = None
        if has_ffmpeg:
            info = MediaService.get_media_info(file_path)
            duration = float(info.get("format", {}).get("duration", 0))
            await _update_job(
                job_id, status=JobStatus.INGESTED,
                duration_seconds=duration,
                file_metadata={"file_size": os.path.getsize(file_path), "media_info": info.get("format", {})},
            )
        else:
            await _update_job(job_id, status=JobStatus.INGESTED,
                              file_metadata={"file_size": os.path.getsize(file_path), "ffmpeg": False})
        logger.info("stage_1_ingest_done", job_id=job_id, duration=duration)

        # ── Stage 2: Audio Enhancement ───────────────────────────────
        if has_ffmpeg:
            await _update_job(job_id, status=JobStatus.EDITING)  # reuse EDITING for audio stage

            enhanced_path = os.path.join(work_dir, "audio_enhanced.mp4")

            # Determine EQ profile from editing style
            eq_profile = "podcast"  # default
            if profile.get("editing_style") == "cinematic":
                eq_profile = "voice"

            await asyncio.to_thread(
                MediaService.enhance_audio,
                current_file, enhanced_path,
                noise_reduction=True,
                noise_floor_db=-40.0,
                eq_profile=eq_profile,
                compress=True,
                de_ess=True,
            )
            current_file = enhanced_path

            # LUFS normalization
            normalized_path = os.path.join(work_dir, "normalized.mp4")
            target_lufs = profile.get("target_lufs", -16.0)
            await asyncio.to_thread(
                MediaService.normalize_audio,
                current_file, target_lufs, normalized_path,
            )
            current_file = normalized_path
            logger.info("stage_2_audio_done", job_id=job_id)

        # ── Stage 3: Color Grading ───────────────────────────────────
        if has_ffmpeg:
            graded_path = os.path.join(work_dir, "color_graded.mp4")

            lut_path = None
            if settings.color_grading_lut_dir:
                # Look for any .cube file in the LUT directory
                lut_dir = settings.color_grading_lut_dir
                if os.path.isdir(lut_dir):
                    cubes = [f for f in os.listdir(lut_dir) if f.endswith(".cube")]
                    if cubes:
                        lut_path = os.path.join(lut_dir, cubes[0])

            await asyncio.to_thread(
                MediaService.color_grade,
                current_file, graded_path,
                auto_correct=True,
                lut_path=lut_path,
                saturation=1.05,  # Slight saturation boost for video podcasts
            )
            current_file = graded_path
            logger.info("stage_3_color_done", job_id=job_id)

        # ── Stage 4: Transcription + Silence Removal ─────────────────
        await _update_job(job_id, status=JobStatus.EDITING)

        transcript = await asyncio.to_thread(_transcribe_audio, file_path)

        if transcript:
            # Save transcript
            transcript_path = os.path.join(work_dir, "transcript.json")
            with open(transcript_path, "w") as f:
                json.dump(transcript, f, indent=2)
            await _update_job(job_id, transcript_url=transcript_path)
            logger.info("transcription_done", job_id=job_id, segments=len(transcript.get("segments", [])))

            # Silence removal
            if has_ffmpeg:
                style_thresholds = {"tight": -25.0, "conversational": -30.0, "cinematic": -35.0}
                threshold = style_thresholds.get(profile.get("editing_style", "conversational"), -30.0)
                min_dur = profile.get("silence_threshold_ms", 1500)

                silences = await asyncio.to_thread(
                    MediaService.detect_silences, current_file, threshold, min_dur,
                )
                if silences:
                    edited_path = os.path.join(work_dir, "edited.mp4")
                    await asyncio.to_thread(
                        MediaService.remove_segments, current_file, silences, edited_path,
                    )
                    current_file = edited_path
                    logger.info("silence_removed", job_id=job_id, segments_removed=len(silences))

        await _update_job(job_id, status=JobStatus.EDITED, edited_file_url=current_file)

        # ── Stage 5: Branding (Intro/Outro/Logo) ─────────────────────
        if has_ffmpeg:
            # Intro
            intro_path = None
            if profile.get("intro_asset_url") and os.path.exists(profile["intro_asset_url"]):
                intro_path = profile["intro_asset_url"]
            elif settings.runway_api_key:
                try:
                    from scout.services.runway import RunwayService
                    runway = RunwayService()
                    intro_path = await runway.generate_intro(
                        brand_name=profile.get("brand_name", "Podcast"),
                        brand_colors={
                            "primary": profile.get("brand_color_primary", "#1a1a2e"),
                            "secondary": profile.get("brand_color_secondary", "#e94560"),
                        },
                        output_path=os.path.join(work_dir, "ai_intro.mp4"),
                    )
                    logger.info("runway_intro_generated", job_id=job_id)
                except Exception as e:
                    logger.warning("runway_intro_failed", error=str(e))

            # Outro
            outro_path = None
            if profile.get("outro_asset_url") and os.path.exists(profile["outro_asset_url"]):
                outro_path = profile["outro_asset_url"]
            elif settings.runway_api_key:
                try:
                    from scout.services.runway import RunwayService
                    runway = RunwayService()
                    outro_path = await runway.generate_outro(
                        brand_name=profile.get("brand_name", "Podcast"),
                        brand_colors={
                            "primary": profile.get("brand_color_primary", "#1a1a2e"),
                            "secondary": profile.get("brand_color_secondary", "#e94560"),
                        },
                        output_path=os.path.join(work_dir, "ai_outro.mp4"),
                    )
                    logger.info("runway_outro_generated", job_id=job_id)
                except Exception as e:
                    logger.warning("runway_outro_failed", error=str(e))

            # Concat intro + main + outro
            parts = [p for p in [intro_path, current_file, outro_path] if p]
            if len(parts) > 1:
                branded_path = os.path.join(work_dir, "branded.mp4")
                await asyncio.to_thread(MediaService.concat_videos, parts, branded_path)
                current_file = branded_path

            # Logo overlay
            logo_url = profile.get("logo_asset_url")
            if logo_url and os.path.exists(logo_url):
                logo_path = os.path.join(work_dir, "with_logo.mp4")
                await asyncio.to_thread(
                    MediaService.apply_logo_overlay,
                    current_file, logo_url, logo_path,
                )
                current_file = logo_path

            logger.info("stage_5_branding_done", job_id=job_id)

        await _update_job(job_id, edited_file_url=current_file)

        # ── Stage 6: AI Clip Analysis ────────────────────────────────
        await _update_job(job_id, status=JobStatus.CLIPPING)

        if not settings.anthropic_api_key:
            await _update_job(job_id, status=JobStatus.FAILED,
                              error_message="ANTHROPIC_API_KEY not set in .env")
            return

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        clips_data = []
        if transcript:
            clips_data = await _run_clip_analysis(client, transcript, profile)
            logger.info("stage_6_clips_identified", job_id=job_id, count=len(clips_data))
        else:
            # No transcript - create a single highlight clip
            clips_data = [{
                "title": "Episode Highlight",
                "description": "Check out this moment!",
                "start_time_seconds": 0,
                "end_time_seconds": min(60, duration or 60),
                "virality_score": 0.7,
                "topics": profile.get("topics", ["podcast"]),
                "transcript_text": "",
            }]

        await _update_job(job_id, status=JobStatus.CLIPPED)

        # ── Stage 7: Render Clips ────────────────────────────────────
        await _update_job(job_id, status=JobStatus.SCHEDULING)  # reuse for rendering stage

        clips_dir = os.path.join(work_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)

        async with async_session_factory() as db:
            for i, clip_data in enumerate(clips_data):
                clip_dir = os.path.join(clips_dir, f"clip_{i}")
                os.makedirs(clip_dir, exist_ok=True)

                start = clip_data.get("start_time_seconds", 0)
                end = clip_data.get("end_time_seconds", 60)

                # Extract clip
                raw_clip = os.path.join(clip_dir, "raw.mp4")
                master_clip = raw_clip
                if has_ffmpeg:
                    try:
                        await asyncio.to_thread(
                            MediaService.extract_clip, current_file, start, end, raw_clip,
                        )
                        master_clip = raw_clip

                        # Burn captions if we have a transcript
                        if transcript:
                            srt_path = os.path.join(clip_dir, "captions.srt")
                            TranscriptionService.transcript_to_srt_for_clip(
                                transcript, srt_path, start, end,
                            )
                            if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
                                captioned = os.path.join(clip_dir, "captioned.mp4")
                                caption_style = profile.get("caption_style", {})
                                await asyncio.to_thread(
                                    MediaService.burn_captions,
                                    raw_clip, srt_path, captioned,
                                    font_size=caption_style.get("font_size", 48),
                                )
                                master_clip = captioned

                        # Platform variants (9:16 for vertical platforms)
                        platform_variants = {}
                        for platform in profile.get("target_platforms", ["tiktok", "instagram", "youtube_shorts"]):
                            if platform in ("tiktok", "instagram", "youtube_shorts"):
                                variant_path = os.path.join(clip_dir, f"{platform}.mp4")
                                await asyncio.to_thread(
                                    MediaService.convert_aspect_ratio,
                                    master_clip, variant_path, 1080, 1920,
                                )
                                platform_variants[platform] = variant_path
                            else:
                                platform_variants[platform] = master_clip

                        # Thumbnail
                        thumb_path = os.path.join(clip_dir, "thumbnail.jpg")
                        mid = (end - start) / 2
                        await asyncio.to_thread(
                            MediaService.generate_thumbnail, raw_clip, thumb_path, mid,
                        )

                    except Exception as e:
                        logger.warning("clip_render_failed", clip=i, error=str(e))
                        master_clip = current_file
                        platform_variants = {}
                        thumb_path = None
                else:
                    master_clip = current_file
                    platform_variants = {}
                    thumb_path = None

                clip = Clip(
                    job_id=uuid_mod.UUID(job_id),
                    user_id=uuid_mod.UUID(user_id),
                    title=clip_data.get("title", f"Clip {i + 1}"),
                    description=clip_data.get("description", ""),
                    start_time_seconds=start,
                    end_time_seconds=end,
                    duration_seconds=end - start,
                    clip_file_url=master_clip,
                    thumbnail_url=thumb_path,
                    platform_variants=platform_variants if platform_variants else None,
                    virality_score=clip_data.get("virality_score", 0.5),
                    topics=clip_data.get("topics", []),
                    transcript_text=clip_data.get("transcript_text", ""),
                    status=ClipStatus.GENERATED,
                )
                db.add(clip)

            await db.commit()
            logger.info("stage_7_clips_rendered", job_id=job_id, count=len(clips_data))

        # ── Stage 8: Complete ────────────────────────────────────────
        await _update_job(
            job_id, status=JobStatus.COMPLETE,
            completed_at=datetime.utcnow(),
        )
        logger.info("pipeline_complete", job_id=job_id)

    except Exception as e:
        logger.error("pipeline_failed", job_id=job_id, error=str(e))
        await _update_job(
            job_id, status=JobStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.utcnow(),
        )


# ── Transcription ────────────────────────────────────────────────────────────

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
                "words": [{"word": w.word, "start": w.start, "end": w.end} for w in (segment.words or [])],
            }
            transcript["segments"].append(seg_data)
        return transcript
    except ImportError:
        logger.warning("faster_whisper_not_installed")
        return None
    except Exception as e:
        logger.error("transcription_failed", error=str(e))
        return None


# ── Claude Clip Analysis ─────────────────────────────────────────────────────

async def _run_clip_analysis(client: anthropic.Anthropic, transcript: dict, profile: dict) -> list[dict]:
    """Use Claude to identify the best viral clips from the transcript."""
    transcript_text = " ".join(seg["text"] for seg in transcript.get("segments", []))
    if not transcript_text.strip():
        return []

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
- "title": catchy scroll-stopping hook title
- "description": engaging social media caption
- "start_time_seconds": approximate start time
- "end_time_seconds": approximate end time
- "virality_score": 0.0 to 1.0
- "topics": relevant topic tags
- "transcript_text": the text of the clip

Return ONLY the JSON array, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
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
