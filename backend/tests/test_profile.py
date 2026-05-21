"""
filename: test_profile.py
author: Equipo Spotify DWH
date: 2025-05-21
version: 1.0
description: Tests del endpoint GET /v1/profile/me.
"""

from unittest.mock import patch

from tests.conftest import MOCK_PROFILE


def test_get_profile_200(client, auth_headers):
    """Perfil con token valido debe retornar 200 y datos del usuario."""
    with patch("app.v1.routers.profile.get_user_profile", return_value=MOCK_PROFILE):
        response = client.get("/v1/profile/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["spotify_id"] == MOCK_PROFILE["spotify_id"]
    assert data["display_name"] == MOCK_PROFILE["display_name"]
    assert data["user_id"] == MOCK_PROFILE["user_id"]


def test_get_profile_no_token_401(client):
    """Sin header Authorization debe rechazar la peticion."""
    response = client.get("/v1/profile/me")

    assert response.status_code in (401, 403)


def test_get_profile_invalid_token_401(client):
    """Token JWT invalido debe retornar 401."""
    response = client.get(
        "/v1/profile/me",
        headers={"Authorization": "Bearer token_invalido"},
    )

    assert response.status_code == 401
