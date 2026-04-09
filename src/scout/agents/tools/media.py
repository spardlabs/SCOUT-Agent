"""Tool definitions for media processing operations."""

MEDIA_TOOLS = [
    {
        "name": "get_media_info",
        "description": "Get metadata about a video/audio file (duration, codec, resolution, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the media file"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "detect_silences",
        "description": "Detect silent segments in a video/audio file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the media file"},
                "threshold_db": {
                    "type": "number",
                    "description": "Volume threshold in dB below which is considered silence",
                    "default": -30.0,
                },
                "min_duration_ms": {
                    "type": "integer",
                    "description": "Minimum silence duration in milliseconds to detect",
                    "default": 1500,
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "remove_segments",
        "description": "Remove specified time segments from a video file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Input video path"},
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                        },
                    },
                    "description": "List of segments to remove, each with start/end in seconds",
                },
                "output_path": {"type": "string", "description": "Output video path"},
            },
            "required": ["file_path", "segments", "output_path"],
        },
    },
    {
        "name": "normalize_audio",
        "description": "Normalize audio levels to a target LUFS value.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Input file path"},
                "target_lufs": {
                    "type": "number",
                    "description": "Target LUFS level (e.g., -16.0)",
                    "default": -16.0,
                },
                "output_path": {"type": "string", "description": "Output file path"},
            },
            "required": ["file_path", "output_path"],
        },
    },
    {
        "name": "extract_clip",
        "description": "Extract a clip from a video between two timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Input video path"},
                "start_seconds": {"type": "number", "description": "Start time in seconds"},
                "end_seconds": {"type": "number", "description": "End time in seconds"},
                "output_path": {"type": "string", "description": "Output clip path"},
            },
            "required": ["file_path", "start_seconds", "end_seconds", "output_path"],
        },
    },
    {
        "name": "convert_aspect_ratio",
        "description": "Convert video to specific dimensions (e.g., 9:16 for TikTok/Reels).",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Input video path"},
                "output_path": {"type": "string", "description": "Output video path"},
                "width": {"type": "integer", "default": 1080},
                "height": {"type": "integer", "default": 1920},
            },
            "required": ["file_path", "output_path"],
        },
    },
    {
        "name": "burn_captions",
        "description": "Burn SRT subtitle captions into a video.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Input video path"},
                "srt_path": {"type": "string", "description": "Path to SRT subtitle file"},
                "output_path": {"type": "string", "description": "Output video path"},
                "font_size": {"type": "integer", "default": 48},
            },
            "required": ["file_path", "srt_path", "output_path"],
        },
    },
    {
        "name": "apply_logo_overlay",
        "description": "Overlay a logo/watermark on a video.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Input video path"},
                "logo_path": {"type": "string", "description": "Path to logo image"},
                "output_path": {"type": "string", "description": "Output video path"},
                "position": {
                    "type": "string",
                    "enum": ["top_left", "top_right", "bottom_left", "bottom_right", "center"],
                    "default": "bottom_right",
                },
                "opacity": {"type": "number", "default": 0.3},
            },
            "required": ["file_path", "logo_path", "output_path"],
        },
    },
]
