"""Tests for database model definitions (schema validation, not DB queries)."""

from scout.db.models.job import JobStatus
from scout.db.models.clip import ClipStatus
from scout.db.models.social_account import Platform
from scout.db.models.post import PostStatus


class TestJobStatus:
    def test_all_statuses_exist(self):
        assert JobStatus.PENDING == "pending"
        assert JobStatus.INGESTING == "ingesting"
        assert JobStatus.INGESTED == "ingested"
        assert JobStatus.EDITING == "editing"
        assert JobStatus.EDITED == "edited"
        assert JobStatus.CLIPPING == "clipping"
        assert JobStatus.CLIPPED == "clipped"
        assert JobStatus.SCHEDULING == "scheduling"
        assert JobStatus.COMPLETE == "complete"
        assert JobStatus.FAILED == "failed"

    def test_status_count(self):
        assert len(JobStatus) == 10


class TestClipStatus:
    def test_all_statuses(self):
        assert ClipStatus.GENERATED == "generated"
        assert ClipStatus.SCHEDULED == "scheduled"
        assert ClipStatus.POSTED == "posted"
        assert ClipStatus.FAILED == "failed"


class TestPlatform:
    def test_all_platforms(self):
        assert Platform.TIKTOK == "tiktok"
        assert Platform.INSTAGRAM == "instagram"
        assert Platform.YOUTUBE == "youtube"
        assert Platform.TWITTER == "twitter"
        assert Platform.LINKEDIN == "linkedin"

    def test_platform_count(self):
        assert len(Platform) == 5


class TestPostStatus:
    def test_all_statuses(self):
        assert PostStatus.SCHEDULED == "scheduled"
        assert PostStatus.POSTING == "posting"
        assert PostStatus.POSTED == "posted"
        assert PostStatus.FAILED == "failed"
