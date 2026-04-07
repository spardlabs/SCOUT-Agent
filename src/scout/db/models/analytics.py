import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scout.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from scout.db.models.post import Post
    from scout.db.models.user import User


class AnalyticsSnapshot(UUIDMixin, Base):
    __tablename__ = "analytics_snapshots"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    watch_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_watch_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    follower_delta: Mapped[int] = mapped_column(Integer, default=0)

    raw_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    post: Mapped["Post"] = relationship(back_populates="analytics_snapshots")


class WeeklyReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "weekly_reports"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)

    report_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)

    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="weekly_reports")
