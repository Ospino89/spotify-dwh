"""
filename: test_artists.py
author: Equipo Spotify DWH
date: 2025-05-21
version: 1.0
description: Tests del endpoint GET /v1/artists/top.
"""

from unittest.mock import patch

from tests.conftest import MOCK_ARTISTS


def test_get_top_artists_200(client, auth_headers):
    """Top artistas con token valido debe retornar 200 y lista de artistas."""
    with patch("app.v1.routers.artists.get_top_artists", return_value=MOCK_ARTISTS):
        response = client.get("/v1/artists/top", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == MOCK_ARTISTS[0]["name"]


def test_get_top_artists_no_token_401(client):
    """Sin token debe rechazar la peticion."""
    response = client.get("/v1/artists/top")

    assert response.status_code in (401, 403)


def test_get_top_artists_invalid_token_401(client):
    """Token invalido debe retornar 401."""
    response = client.get(
        "/v1/artists/top",
        headers={"Authorization": "Bearer token_invalido"},
    )

    assert response.status_code == 401


def test_get_top_artists_empty_returns_200(client, auth_headers):
    """Lista vacia de artistas debe retornar 200 con array vacio."""
    with patch("app.v1.routers.artists.get_top_artists", return_value=[]):
        response = client.get("/v1/artists/top", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
