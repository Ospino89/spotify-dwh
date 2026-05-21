"""
filename: test_auth.py
author: Equipo Spotify DWH
date: 2025-05-21
version: 1.0
description: Tests del router de autenticacion OAuth PKCE.
"""

from unittest.mock import patch

from tests.conftest import MOCK_SPOTIFY_ID


def test_login_redirects(client):
    """GET /v1/auth/login debe redirigir a Spotify con status 302."""
    spotify_url = "https://accounts.spotify.com/authorize?response_type=code"

    with (
        patch("app.v1.routers.auth.save_pkce_session"),
        patch("app.v1.routers.auth.generate_pkce_pair", return_value=("verifier", "challenge")),
        patch("app.v1.routers.auth.generate_state", return_value="test-state-uuid"),
        patch("app.v1.routers.auth.build_spotify_auth_url", return_value=spotify_url),
    ):
        response = client.get("/v1/auth/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == spotify_url


def test_callback_returns_jwt(client):
    """GET /v1/auth/callback debe redirigir al frontend con token JWT en la URL."""
    with (
        patch(
            "app.v1.routers.auth.get_pkce_session",
            return_value={"state": "valid-state", "verifier": "test-verifier"},
        ),
        patch(
            "app.v1.routers.auth.exchange_code_for_tokens",
            return_value={
                "access_token": "spotify_access",
                "refresh_token": "spotify_refresh",
                "expires_in": 3600,
            },
        ),
        patch(
            "app.v1.routers.auth.spotify_get",
            return_value={"id": MOCK_SPOTIFY_ID, "display_name": "Test User"},
        ),
        patch("app.v1.routers.auth.upsert_user_with_tokens", return_value=MOCK_SPOTIFY_ID),
    ):
        response = client.get(
            "/v1/auth/callback?code=auth_code_123&state=valid-state",
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers["location"]
    assert "token=" in location
    assert location.startswith("http://localhost:3000")


def test_callback_invalid_state_401(client):
    """Callback con state invalido debe retornar 401."""
    with patch("app.v1.routers.auth.get_pkce_session", return_value=None):
        response = client.get(
            "/v1/auth/callback?code=auth_code_123&state=invalid-state",
            follow_redirects=False,
        )

    assert response.status_code == 401
    assert "State invalido" in response.json()["detail"]
