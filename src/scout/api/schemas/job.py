import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    source_filename: str
    raw_file_url: Optional[str] = None
    edited_file_url: Optional[str] = None
    transcript_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_metadata: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
