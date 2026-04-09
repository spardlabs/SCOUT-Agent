"""Tests for FastAPI API routes using TestClient."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from scout.main import app
from scout.db.session import get_db


def _mock_db_session():
    """Create a mock async DB session."""
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []
    result.scalar_one.return_value = 0
    session.execute.return_value = result
    return session


@pytest.fixture
def client():
    mock_session = _mock_db_session()

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "scout-agent"


class TestUserRoutes:
    def test_create_user_returns_api_key(self, client):
        """Test user creation endpoint returns a user and API key."""
        mock_session = _mock_db_session()

        # Make flush/refresh populate the user object
        original_add = mock_session.add

        async def mock_flush():
            pass

        async def mock_refresh(obj):
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = uuid.uuid4()
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = datetime(2025, 1, 1)

        mock_session.flush = mock_flush
        mock_session.refresh = mock_refresh

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/users",
            json={"email": "test@example.com", "name": "Test User"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("sk_scout_")
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Test User"

        app.dependency_overrides.clear()


class TestWebhookRoutes:
    def test_dropbox_webhook_verify(self, client):
        """Dropbox sends a GET with challenge for verification."""
        response = client.get("/api/webhooks/dropbox?challenge=test_challenge_123")
        assert response.status_code == 200
        assert response.json()["challenge"] == "test_challenge_123"


class TestProfileCreate:
    def test_profile_schema_defaults(self):
        """Verify profile creation with default values."""
        from scout.api.schemas.profile import ProfileCreate

        profile = ProfileCreate()
        assert profile.editing_style == "conversational"
        assert profile.target_lufs == -16.0
