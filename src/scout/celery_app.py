from celery import Celery
from celery.schedules import crontab

from scout.config import settings


def create_celery_app() -> Celery:
    app = Celery(
        "scout",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )

    # Auto-discover tasks
    app.autodiscover_tasks(["scout.tasks"])

    # Celery Beat schedule
    app.conf.beat_schedule = {
        # Execute scheduled posts every minute
        "execute-due-posts": {
            "task": "scout.tasks.posting.execute_due_posts",
            "schedule": 60.0,
        },
        # Collect analytics daily at 6 AM UTC
        "collect-daily-analytics": {
            "task": "scout.tasks.analytics.collect_daily_metrics",
            "schedule": crontab(hour=6, minute=0),
        },
        # Generate weekly reports every Monday at 8 AM UTC
        "generate-weekly-reports": {
            "task": "scout.tasks.analytics.generate_weekly_reports",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),
        },
    }

    return app


celery_app = create_celery_app()
