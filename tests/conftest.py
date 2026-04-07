import pytest


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing clip selection."""
    return {
        "language": "en",
        "language_probability": 0.98,
        "duration": 3600.0,
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 15.0,
                "text": "Welcome to the show everyone, today we're going to talk about AI and how it's changing everything.",
                "words": [
                    {"word": "Welcome", "start": 0.0, "end": 0.5, "probability": 0.99},
                    {"word": "to", "start": 0.5, "end": 0.6, "probability": 0.99},
                    {"word": "the", "start": 0.6, "end": 0.7, "probability": 0.99},
                    {"word": "show", "start": 0.7, "end": 1.0, "probability": 0.99},
                ],
            },
            {
                "id": 1,
                "start": 120.0,
                "end": 180.0,
                "text": "The thing that blew my mind is that AI can now write code better than most developers. That's not an exaggeration.",
                "words": [],
            },
            {
                "id": 2,
                "start": 300.0,
                "end": 360.0,
                "text": "Here's my advice for anyone starting a business: don't wait for the perfect idea. Start with what you have and iterate fast.",
                "words": [],
            },
        ],
    }


@pytest.fixture
def sample_profile():
    """Sample editing profile for testing."""
    return {
        "silence_threshold_ms": 1500,
        "silence_action": "remove",
        "target_lufs": -16.0,
        "editing_style": "conversational",
        "topics": ["AI", "startups", "technology"],
        "virality_preferences": {"humor": 0.5, "controversy": 0.3, "education": 0.8},
        "target_platforms": ["tiktok", "instagram", "youtube_shorts"],
        "clip_length_range": {"min_seconds": 30, "max_seconds": 90},
        "caption_style": {
            "position": "bottom",
            "font_size": 48,
            "color": "#FFFFFF",
            "bg_color": "#000000AA",
            "animation": "word_highlight",
        },
    }
