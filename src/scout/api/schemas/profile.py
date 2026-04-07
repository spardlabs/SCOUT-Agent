import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    silence_threshold_ms: int = 1500
    silence_action: str = "remove"
    target_lufs: float = -16.0
    intro_asset_url: Optional[str] = None
    outro_asset_url: Optional[str] = None
    logo_asset_url: Optional[str] = None
    brand_color_primary: str = "#1a1a2e"
    brand_color_secondary: str = "#e94560"
    brand_font: str = "Montserrat-Bold"
    caption_style: dict[str, Any] = {
        "position": "bottom",
        "font_size": 48,
        "color": "#FFFFFF",
        "bg_color": "#000000AA",
        "animation": "word_highlight",
    }
    topics: list[str] = []
    virality_preferences: dict[str, Any] = {
        "humor": 0.5,
        "controversy": 0.2,
        "education": 0.7,
    }
    target_platforms: list[str] = ["tiktok", "instagram", "youtube_shorts"]
    clip_length_range: dict[str, int] = {"min_seconds": 30, "max_seconds": 90}
    editing_style: str = "conversational"


class ProfileUpdate(BaseModel):
    silence_threshold_ms: Optional[int] = None
    silence_action: Optional[str] = None
    target_lufs: Optional[float] = None
    intro_asset_url: Optional[str] = None
    outro_asset_url: Optional[str] = None
    logo_asset_url: Optional[str] = None
    brand_color_primary: Optional[str] = None
    brand_color_secondary: Optional[str] = None
    brand_font: Optional[str] = None
    caption_style: Optional[dict[str, Any]] = None
    topics: Optional[list[str]] = None
    virality_preferences: Optional[dict[str, Any]] = None
    target_platforms: Optional[list[str]] = None
    clip_length_range: Optional[dict[str, int]] = None
    editing_style: Optional[str] = None


class ProfileResponse(ProfileCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
