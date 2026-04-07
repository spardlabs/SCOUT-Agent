"""Tests for configuration module."""

from scout.config import Settings


class TestConfig:
    def test_default_values(self):
        s = Settings(
            _env_file=None,  # Don't load .env
        )
        assert s.app_env == "development"
        assert s.s3_bucket_name == "scout-media"
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_sync_database_url(self):
        s = Settings(_env_file=None)
        sync_url = s.sync_database_url
        assert "+asyncpg" not in sync_url
        assert "postgresql://" in sync_url
