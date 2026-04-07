import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scout.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from scout.db.models.clip import Clip
    from scout.db.models.user import User


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    INGESTED = "ingested"
    EDITING = "editing"
    EDITED = "edited"
    CLIPPING = "clipping"
    CLIPPED = "clipped"
    SCHEDULING = "scheduling"
    COMPLETE = "complete"
    FAILED = "failed"


class Job(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False
    )

    # File references (S3 paths)
    raw_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    edited_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transcript_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata
    source_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="jobs")
    clips: Mapped[list["Clip"]] = relationship(back_populates="job", cascade="all, delete-orphan")
