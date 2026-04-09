import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scout.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from scout.db.models.post import Post
    from scout.db.models.user import User


class Platform(str, enum.Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


class SocialAccount(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "social_accounts"
    __table_args__ = (
        # One account per platform per user
        {"comment": "User social media account connections"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_username: Mapped[str] = mapped_column(String(255), nullable=False)

    # Encrypted OAuth tokens
    access_token_encrypted: Mapped[str] = mapped_column(String(1000), nullable=False)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scopes: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="social_accounts")
    posts: Mapped[list["Post"]] = relationship(
        back_populates="social_account", cascade="all, delete-orphan"
    )
