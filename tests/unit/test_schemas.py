"""Tests for Pydantic API schemas."""

import uuid
from datetime import datetime

from pydantic import ValidationError
import pytest

from scout.api.schemas.user import UserCreate, UserResponse
from scout.api.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from scout.api.schemas.job import JobResponse
from scout.api.schemas.clip import ClipResponse


class TestUserSchemas:
    def test_user_create_valid(self):
        user = UserCreate(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    def test_user_create_requires_fields(self):
        with pytest.raises(ValidationError):
            UserCreate()

    def test_user_response_from_attributes(self):
        data = {
            "id": uuid.uuid4(),
            "email": "test@example.com",
            "name": "Test",
            "created_at": datetime.utcnow(),
        }
        resp = UserResponse(**data)
        assert resp.email == "test@example.com"


class TestProfileSchemas:
    def test_profile_create_defaults(self):
        profile = ProfileCreate()
        assert profile.silence_threshold_ms == 1500
        assert profile.target_lufs == -16.0
        assert profile.editing_style == "conversational"
        assert "tiktok" in profile.target_platforms
        assert profile.clip_length_range["min_seconds"] == 30

    def test_profile_create_custom_values(self):
        profile = ProfileCreate(
            silence_threshold_ms=800,
            editing_style="tight",
            topics=["tech", "gaming"],
            virality_preferences={"humor": 0.9, "education": 0.3, "controversy": 0.1},
        )
        assert profile.silence_threshold_ms == 800
        assert profile.editing_style == "tight"
        assert "gaming" in profile.topics

    def test_profile_update_partial(self):
        update = ProfileUpdate(editing_style="cinematic")
        data = update.model_dump(exclude_unset=True)
        assert data == {"editing_style": "cinematic"}
        assert "silence_threshold_ms" not in data

    def test_profile_update_empty(self):
        update = ProfileUpdate()
        data = update.model_dump(exclude_unset=True)
        assert data == {}


class TestJobSchemas:
    def test_job_response_with_nulls(self):
        data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "status": "pending",
            "source_filename": "episode.mp4",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        job = JobResponse(**data)
        assert job.edited_file_url is None
        assert job.error_message is None


class TestClipSchemas:
    def test_clip_response_full(self):
        data = {
            "id": uuid.uuid4(),
            "job_id": uuid.uuid4(),
            "title": "Mind-blowing AI take",
            "start_time_seconds": 120.5,
            "end_time_seconds": 180.0,
            "duration_seconds": 59.5,
            "clip_file_url": "s3://bucket/clip.mp4",
            "virality_score": 0.92,
            "topics": ["AI", "tech"],
            "status": "generated",
            "created_at": datetime.utcnow(),
        }
        clip = ClipResponse(**data)
        assert clip.virality_score == 0.92
        assert clip.duration_seconds == 59.5
