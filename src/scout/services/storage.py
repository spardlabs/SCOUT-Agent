import os
from typing import BinaryIO

import boto3
from botocore.config import Config

from scout.config import settings
from scout.core.exceptions import StorageError
from scout.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Abstraction over S3/MinIO for file storage."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.s3_bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info("bucket_created", bucket=self.bucket)
            except Exception as e:
                logger.warning("bucket_create_failed", error=str(e))

    def upload_file(self, file_obj: BinaryIO, key: str, content_type: str = "video/mp4") -> str:
        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            url = f"s3://{self.bucket}/{key}"
            logger.info("file_uploaded", key=key)
            return url
        except Exception as e:
            raise StorageError(f"Failed to upload {key}: {e}") from e

    def upload_from_path(self, local_path: str, key: str, content_type: str = "video/mp4") -> str:
        try:
            self.client.upload_file(
                local_path,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            url = f"s3://{self.bucket}/{key}"
            logger.info("file_uploaded", key=key, source=local_path)
            return url
        except Exception as e:
            raise StorageError(f"Failed to upload {local_path}: {e}") from e

    def download_file(self, key: str, local_path: str) -> str:
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.client.download_file(self.bucket, key, local_path)
            logger.info("file_downloaded", key=key, dest=local_path)
            return local_path
        except Exception as e:
            raise StorageError(f"Failed to download {key}: {e}") from e

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def key_from_url(self, s3_url: str) -> str:
        """Extract S3 key from s3://bucket/key URL."""
        prefix = f"s3://{self.bucket}/"
        if s3_url.startswith(prefix):
            return s3_url[len(prefix):]
        return s3_url
