class ScoutError(Exception):
    """Base exception for SCOUT-Agent."""


class StorageError(ScoutError):
    """Error during file storage operations."""


class MediaProcessingError(ScoutError):
    """Error during media processing (FFmpeg, transcription, etc.)."""


class AgentError(ScoutError):
    """Error during agent execution."""


class SocialPlatformError(ScoutError):
    """Error during social media API operations."""


class WebhookValidationError(ScoutError):
    """Invalid or unverifiable webhook payload."""
