import enum
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scout.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from scout.db.models.job import Job
    from scout.db.models.post import Post


class ClipStatus(str, enum.Enum):
    GENERATED = "generated"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"


class Clip(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "clips"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps in the original video
    start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    # Files
    clip_file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    platform_variants: Mapped[Optional[dict[str, str]]] = mapped_column(JSONB, nullable=True)

    # AI analysis
    virality_score: Mapped[float] = mapped_column(Float, default=0.0)
    topics: Mapped[list[str]] = mapped_column(JSONB, default=list)
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[ClipStatus] = mapped_column(
        Enum(ClipStatus), default=ClipStatus.GENERATED, nullable=False
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="clips")
    posts: Mapped[list["Post"]] = relationship(back_populates="clip", cascade="all, delete-orphan")
