"""Tests for Celery app configuration."""

from scout.celery_app import celery_app


class TestCeleryConfig:
    def test_celery_app_name(self):
        assert celery_app.main == "scout"

    def test_task_serializer_json(self):
        assert celery_app.conf.task_serializer == "json"

    def test_timezone_utc(self):
        assert celery_app.conf.timezone == "UTC"

    def test_beat_schedule_has_required_tasks(self):
        schedule = celery_app.conf.beat_schedule
        assert "execute-due-posts" in schedule
        assert "collect-daily-analytics" in schedule
        assert "generate-weekly-reports" in schedule

    def test_due_posts_runs_every_minute(self):
        schedule = celery_app.conf.beat_schedule["execute-due-posts"]
        assert schedule["schedule"] == 60.0
        assert schedule["task"] == "scout.tasks.posting.execute_due_posts"
