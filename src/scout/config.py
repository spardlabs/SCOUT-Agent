from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://scout:scout_dev@localhost:5432/scout"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "scout-media"
    s3_region: str = "us-east-1"

    # Anthropic
    anthropic_api_key: str = ""

    # Dropbox
    dropbox_app_key: str = ""
    dropbox_app_secret: str = ""
    dropbox_webhook_secret: str = ""

    # Google Drive
    google_client_id: str = ""
    google_client_secret: str = ""

    # Social Media - TikTok
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""

    # Social Media - Instagram / Meta
    meta_app_id: str = ""
    meta_app_secret: str = ""

    # Social Media - Twitter / X
    twitter_api_key: str = ""
    twitter_api_secret: str = ""

    # Social Media - LinkedIn
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""

    # Sentry
    sentry_dsn: str = ""

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
