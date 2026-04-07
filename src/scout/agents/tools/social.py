"""Tool definitions for social media operations."""

SOCIAL_TOOLS = [
    {
        "name": "get_optimal_posting_times",
        "description": "Analyze historical engagement data to determine optimal posting times for each platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID to analyze"},
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "instagram", "youtube", "twitter", "linkedin"],
                    "description": "Social media platform",
                },
            },
            "required": ["user_id", "platform"],
        },
    },
    {
        "name": "schedule_post",
        "description": "Schedule a clip to be posted to a social media platform at a specific time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_id": {"type": "string", "description": "Clip ID to post"},
                "social_account_id": {"type": "string", "description": "Social account to post to"},
                "scheduled_at": {"type": "string", "description": "ISO datetime for when to post"},
                "caption_text": {"type": "string", "description": "Post caption text"},
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of hashtags",
                },
            },
            "required": ["clip_id", "social_account_id", "scheduled_at", "caption_text"],
        },
    },
    {
        "name": "fetch_platform_metrics",
        "description": "Fetch current metrics for a posted video from the platform API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_id": {"type": "string", "description": "Internal post record ID"},
            },
            "required": ["post_id"],
        },
    },
    {
        "name": "generate_report",
        "description": "Generate a weekly analytics report for a user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"},
                "week_start": {"type": "string", "description": "Start of reporting week (ISO date)"},
                "week_end": {"type": "string", "description": "End of reporting week (ISO date)"},
            },
            "required": ["user_id", "week_start", "week_end"],
        },
    },
]
