"""Tool definitions for transcription operations."""

TRANSCRIPT_TOOLS = [
    {
        "name": "transcribe_audio",
        "description": "Transcribe audio/video file using Whisper. Returns word-level timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to audio/video file"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "search_transcript",
        "description": "Search the transcript for segments matching a query or topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transcript": {
                    "type": "object",
                    "description": "The full transcript object",
                },
                "query": {
                    "type": "string",
                    "description": "Topic or keyword to search for",
                },
            },
            "required": ["transcript", "query"],
        },
    },
    {
        "name": "generate_srt",
        "description": "Generate an SRT subtitle file from a transcript.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transcript": {"type": "object", "description": "The transcript object"},
                "output_path": {"type": "string", "description": "Output SRT file path"},
            },
            "required": ["transcript", "output_path"],
        },
    },
]
