"""
filename: conftest.py
author: Equipo Spotify DWH
date: 2025-05-21
version: 1.0
description: Fixtures compartidos para pytest: app, client, token JWT y mock de DB.
"""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Variables de entorno de prueba (antes de importar la app)
_TEST_ENV = {
    "SPOTIFY_CLIENT_ID": "test_client_id",
    "SPOTIFY_CLIENT_SECRET": "test_client_secret",
    "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8000/v1/auth/callback",
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
    "APP_NAME": "Test Spotify DWH",
    "APP_VERSION": "0.0.1-test",
    "SECRET_KEY": "test_secret_key_minimum_32_chars_long",
    "FRONTEND_URL": "http://localhost:3000",
}
for _key, _value in _TEST_ENV.items():
    os.environ[_key] = _value

from main import app  # noqa: E402
from app.core.database import get_db_dependency  # noqa: E402
from app.core.security import create_access_token  # noqa: E402

MOCK_SPOTIFY_ID = "spotify_user_test_123"

MOCK_PROFILE = {
    "user_id": 1,
    "spotify_id": MOCK_SPOTIFY_ID,
    "display_name": "Test User",
    "email": "test@example.com",
    "country": "CO",
    "followers": 42,
    "product": "premium",
    "loaded_at": datetime(2025, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
}

MOCK_ARTISTS = [
    {
        "artist_id": 1,
        "spotify_id": "artist_spotify_1",
        "name": "Mock Artist",
        "popularity": 85,
        "followers_count": 1000000,
        "genres": ["pop", "rock"],
        "loaded_at": datetime(2025, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
    }
]

MOCK_TRACKS = [
    {
        "track_id": 1,
        "spotify_id": "track_spotify_1",
        "name": "Mock Track",
        "artist_id": 1,
        "album_name": "Mock Album",
        "duration_ms": 210000,
        "popularity": 90,
        "explicit": False,
        "loaded_at": datetime(2025, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
    }
]

MOCK_HISTORY = [
    {
        "id": 1,
        "user_id": 1,
        "track_id": 1,
        "artist_id": 1,
        "played_at": datetime(2025, 5, 10, 18, 30, 0, tzinfo=timezone.utc),
        "hour_of_day": 18,
        "day_of_week": 5,
        "context_type": "playlist",
        "track_spotify_id": "track_spotify_1",
        "artist_spotify_id": "artist_spotify_1",
    }
]


@pytest.fixture
def mock_db():
    """Conexion PostgreSQL simulada para no requerir Neon en tests."""
    return MagicMock()


@pytest.fixture(autouse=True)
def override_db(mock_db):
    """Sustituye get_db_dependency por un mock en todos los tests."""
    def _override():
        yield mock_db

    app.dependency_overrides[get_db_dependency] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Cliente HTTP de prueba contra la app FastAPI."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """JWT valido firmado con el secret de prueba."""
    return create_access_token(MOCK_SPOTIFY_ID)


@pytest.fixture
def auth_headers(valid_token):
    """Header Authorization listo para endpoints protegidos."""
    return {"Authorization": f"Bearer {valid_token}"}
