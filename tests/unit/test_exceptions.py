"""Tests for custom exception hierarchy."""

from scout.core.exceptions import (
    AgentError,
    MediaProcessingError,
    ScoutError,
    SocialPlatformError,
    StorageError,
    WebhookValidationError,
)


class TestExceptions:
    def test_all_inherit_from_scout_error(self):
        for exc_class in [StorageError, MediaProcessingError, AgentError,
                          SocialPlatformError, WebhookValidationError]:
            assert issubclass(exc_class, ScoutError)

    def test_scout_error_inherits_from_exception(self):
        assert issubclass(ScoutError, Exception)

    def test_exceptions_carry_message(self):
        e = MediaProcessingError("ffmpeg failed")
        assert str(e) == "ffmpeg failed"

    def test_exceptions_are_catchable_by_base(self):
        try:
            raise StorageError("upload failed")
        except ScoutError as e:
            assert "upload failed" in str(e)
