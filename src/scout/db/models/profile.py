import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scout.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from scout.db.models.user import User


class EditingProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "editing_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    # Silence handling
    silence_threshold_ms: Mapped[int] = mapped_column(Integer, default=1500)
    silence_action: Mapped[str] = mapped_column(String(20), default="remove")  # remove | shorten

    # Audio
    target_lufs: Mapped[float] = mapped_column(Float, default=-16.0)

    # Branding assets (S3 paths)
    intro_asset_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    outro_asset_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_asset_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Visual branding
    brand_color_primary: Mapped[str] = mapped_column(String(7), default="#1a1a2e")
    brand_color_secondary: Mapped[str] = mapped_column(String(7), default="#e94560")
    brand_font: Mapped[str] = mapped_column(String(100), default="Montserrat-Bold")

    # Caption style: {position, font_size, color, bg_color, animation}
    caption_style: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {
            "position": "bottom",
            "font_size": 48,
            "color": "#FFFFFF",
            "bg_color": "#000000AA",
            "animation": "word_highlight",
        },
    )

    # Content preferences
    topics: Mapped[list[str]] = mapped_column(JSONB, default=list)
    virality_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {"humor": 0.5, "controversy": 0.2, "education": 0.7},
    )
    target_platforms: Mapped[list[str]] = mapped_column(
        JSONB,
        default=lambda: ["tiktok", "instagram", "youtube_shorts"],
    )
    clip_length_range: Mapped[dict[str, int]] = mapped_column(
        JSONB,
        default=lambda: {"min_seconds": 30, "max_seconds": 90},
    )
    editing_style: Mapped[str] = mapped_column(
        String(30), default="conversational"
    )  # tight | conversational | cinematic

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")
