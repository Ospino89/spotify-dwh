"""
filename: test_tracks.py
author: Equipo Spotify DWH
date: 2025-05-21
version: 1.0
description: Tests del endpoint GET /v1/tracks/top.
"""

from unittest.mock import patch

from tests.conftest import MOCK_TRACKS


def test_get_top_tracks_200(client, auth_headers):
    """Top tracks con token valido debe retornar 200 y lista de tracks."""
    with patch("app.v1.routers.tracks.get_top_tracks", return_value=MOCK_TRACKS):
        response = client.get("/v1/tracks/top", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == MOCK_TRACKS[0]["name"]


def test_get_top_tracks_no_token_401(client):
    """Sin token debe rechazar la peticion."""
    response = client.get("/v1/tracks/top")

    assert response.status_code in (401, 403)


def test_get_top_tracks_invalid_token_401(client):
    """Token invalido debe retornar 401."""
    response = client.get(
        "/v1/tracks/top",
        headers={"Authorization": "Bearer token_invalido"},
    )

    assert response.status_code == 401


def test_get_top_tracks_empty_returns_200(client, auth_headers):
    """Lista vacia de tracks debe retornar 200 con array vacio."""
    with patch("app.v1.routers.tracks.get_top_tracks", return_value=[]):
        response = client.get("/v1/tracks/top", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
