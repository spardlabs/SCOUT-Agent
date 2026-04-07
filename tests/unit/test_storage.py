"""Tests for storage service."""

from unittest.mock import MagicMock, patch

import pytest

from scout.services.storage import StorageService


class TestStorageService:
    @patch("scout.services.storage.boto3")
    def test_key_from_url(self, mock_boto3):
        mock_boto3.client.return_value = MagicMock()
        service = StorageService()
        key = service.key_from_url("s3://scout-media/raw/user123/job456/file.mp4")
        assert key == "raw/user123/job456/file.mp4"

    @patch("scout.services.storage.boto3")
    def test_key_from_url_passthrough(self, mock_boto3):
        """If URL doesn't match bucket prefix, return as-is."""
        mock_boto3.client.return_value = MagicMock()
        service = StorageService()
        key = service.key_from_url("some/other/key.mp4")
        assert key == "some/other/key.mp4"

    @patch("scout.services.storage.boto3")
    def test_upload_from_path_returns_s3_url(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        service = StorageService()

        result = service.upload_from_path("/tmp/video.mp4", "raw/u/j/video.mp4")

        mock_client.upload_file.assert_called_once()
        assert result.startswith("s3://")
        assert "raw/u/j/video.mp4" in result

    @patch("scout.services.storage.boto3")
    def test_download_file_creates_directories(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        service = StorageService()

        with patch("os.makedirs") as mock_makedirs:
            service.download_file("key.mp4", "/tmp/deep/nested/file.mp4")
            mock_makedirs.assert_called_once()

    @patch("scout.services.storage.boto3")
    def test_get_presigned_url(self, mock_boto3):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://presigned.example.com/file"
        mock_boto3.client.return_value = mock_client
        service = StorageService()

        url = service.get_presigned_url("raw/file.mp4", expires_in=7200)

        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "scout-media", "Key": "raw/file.mp4"},
            ExpiresIn=7200,
        )
        assert url == "https://presigned.example.com/file"
