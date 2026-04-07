import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scout.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from scout.db.models.analytics import AnalyticsSnapshot
    from scout.db.models.clip import Clip
    from scout.db.models.social_account import SocialAccount


class PostStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"


class Post(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "posts"

    clip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_accounts.id"), nullable=False
    )

    platform_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_post_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.SCHEDULED, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    caption_text: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # Relationships
    clip: Mapped["Clip"] = relationship(back_populates="posts")
    social_account: Mapped["SocialAccount"] = relationship(back_populates="posts")
    analytics_snapshots: Mapped[list["AnalyticsSnapshot"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
