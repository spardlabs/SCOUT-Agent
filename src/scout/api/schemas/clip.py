import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClipResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    title: str
    description: Optional[str] = None
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    clip_file_url: str
    thumbnail_url: Optional[str] = None
    platform_variants: Optional[dict[str, str]] = None
    virality_score: float
    topics: list[str]
    transcript_text: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClipListResponse(BaseModel):
    clips: list[ClipResponse]
    total: int
