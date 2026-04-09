"""Tests for social platform base and adapter wiring."""

from scout.services.social.base import MetricsResult, PostResult, SocialPlatform


class TestPostResult:
    def test_post_result_fields(self):
        result = PostResult(
            platform_post_id="123",
            platform_post_url="https://tiktok.com/123",
            raw_response={"id": "123"},
        )
        assert result.platform_post_id == "123"
        assert result.platform_post_url == "https://tiktok.com/123"


class TestMetricsResult:
    def test_metrics_defaults(self):
        metrics = MetricsResult()
        assert metrics.views == 0
        assert metrics.likes == 0
        assert metrics.saves is None
        assert metrics.watch_time_seconds is None

    def test_metrics_with_values(self):
        metrics = MetricsResult(
            views=10000,
            likes=500,
            comments=50,
            shares=100,
            saves=200,
            avg_watch_percentage=0.75,
        )
        assert metrics.views == 10000
        assert metrics.avg_watch_percentage == 0.75


class TestSocialPlatformABC:
    def test_cannot_instantiate_abstract(self):
        """SocialPlatform is abstract and can't be instantiated."""
        import pytest
        with pytest.raises(TypeError):
            SocialPlatform()
