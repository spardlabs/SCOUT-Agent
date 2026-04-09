"""Tool definitions for storage operations."""

STORAGE_TOOLS = [
    {
        "name": "upload_to_storage",
        "description": "Upload a local file to S3 storage. Returns the S3 URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "local_path": {
                    "type": "string",
                    "description": "Path to the local file to upload",
                },
                "s3_key": {
                    "type": "string",
                    "description": "The S3 key (path) to store the file at",
                },
                "content_type": {
                    "type": "string",
                    "description": "MIME type of the file",
                    "default": "video/mp4",
                },
            },
            "required": ["local_path", "s3_key"],
        },
    },
    {
        "name": "download_from_storage",
        "description": "Download a file from S3 storage to local disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "s3_key": {
                    "type": "string",
                    "description": "The S3 key to download",
                },
                "local_path": {
                    "type": "string",
                    "description": "Local path to save the file",
                },
            },
            "required": ["s3_key", "local_path"],
        },
    },
]
