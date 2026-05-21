"""
filename: test_history.py
author: Equipo Spotify DWH
date: 2025-05-21
version: 1.0
description: Tests del endpoint GET /v1/history/recently-played.
"""

from unittest.mock import patch

from tests.conftest import MOCK_HISTORY


def test_recently_played_200(client, auth_headers):
    """Historial con token valido debe retornar 200 y lista de reproducciones."""
    with patch("app.v1.routers.history.get_listening_history", return_value=MOCK_HISTORY):
        response = client.get("/v1/history/recently-played", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["hour_of_day"] == MOCK_HISTORY[0]["hour_of_day"]


def test_recently_played_no_token_401(client):
    """Sin token debe rechazar la peticion."""
    response = client.get("/v1/history/recently-played")

    assert response.status_code in (401, 403)


def test_recently_played_invalid_token_401(client):
    """Token invalido debe retornar 401."""
    response = client.get(
        "/v1/history/recently-played",
        headers={"Authorization": "Bearer token_invalido"},
    )

    assert response.status_code == 401


def test_empty_history_200(client, auth_headers):
    """Historial vacio debe retornar 200 con array vacio."""
    with patch("app.v1.routers.history.get_listening_history", return_value=[]):
        response = client.get("/v1/history/recently-played", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
