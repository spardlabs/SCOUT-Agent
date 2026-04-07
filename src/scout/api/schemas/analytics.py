import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class AnalyticsSnapshotResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    captured_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    saves: Optional[int] = None
    watch_time_seconds: Optional[float] = None
    avg_watch_percentage: Optional[float] = None
    follower_delta: int

    model_config = {"from_attributes": True}


class WeeklyReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    week_end: date
    report_data: dict[str, Any]
    narrative: str
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WeeklyReportListResponse(BaseModel):
    reports: list[WeeklyReportResponse]
    total: int
