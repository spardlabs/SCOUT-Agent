#!/usr/bin/env python3
"""Seed the database with a test user and editing profile."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


async def main():
    from scout.db.session import async_session_factory
    from scout.db.models.user import User
    from scout.db.models.profile import EditingProfile
    from scout.core.auth import generate_api_key, hash_api_key

    async with async_session_factory() as db:
        # Create test user
        api_key = generate_api_key()
        user = User(
            email="test@example.com",
            name="Test Creator",
            api_key_hash=hash_api_key(api_key),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        # Create editing profile
        profile = EditingProfile(
            user_id=user.id,
            silence_threshold_ms=1200,
            target_lufs=-16.0,
            editing_style="tight",
            topics=["tech", "AI", "startups"],
            virality_preferences={"humor": 0.7, "controversy": 0.3, "education": 0.9},
            target_platforms=["tiktok", "instagram", "youtube_shorts", "twitter", "linkedin"],
            clip_length_range={"min_seconds": 30, "max_seconds": 90},
        )
        db.add(profile)
        await db.commit()

        print(f"Created test user: {user.email}")
        print(f"User ID: {user.id}")
        print(f"API Key: {api_key}")
        print("(Save this key - it won't be shown again)")


if __name__ == "__main__":
    asyncio.run(main())
