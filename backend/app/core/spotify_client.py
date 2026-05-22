"""
filename: spotify_client.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Cliente HTTP reutilizable para consumir la Spotify Web API.
             Todas las llamadas autenticadas pasan por este modulo.
"""

import time
import httpx

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"


def get_auth_headers(access_token: str) -> dict:
    """
    Construye los headers de autorizacion para llamadas a la Spotify API.

    Args:
        access_token (str): Access token de Spotify (Bearer).

    Returns:
        dict: Headers con Authorization: Bearer <token>.
    """
    return {"Authorization": f"Bearer {access_token}"}


def spotify_get(endpoint: str, access_token: str, params: dict = None) -> dict:
    """
    Realiza una peticion GET autenticada a la Spotify API.

    Args:
        endpoint (str): Path del endpoint relativo a la base URL, ej. '/me'.
        access_token (str): Access token de Spotify.
        params (dict): Query parameters opcionales.

    Returns:
        dict: Respuesta JSON de Spotify.

    Raises:
        httpx.HTTPStatusError: Si Spotify retorna un error HTTP (4xx, 5xx).
    """
    return _spotify_get_once(endpoint, access_token, params)


def _spotify_get_once(endpoint: str, access_token: str, params: dict | None) -> dict:
    url = f"{SPOTIFY_API_BASE}{endpoint}"
    with httpx.Client() as client:
        response = client.get(url, headers=get_auth_headers(access_token), params=params or {})
        response.raise_for_status()
        return response.json()


def spotify_get_with_retry(
    endpoint: str,
    access_token: str,
    params: dict | None = None,
    *,
    max_retries: int = 3,
) -> dict:
    """GET con reintentos solo ante 429 (rate limit)."""
    last_err: httpx.HTTPStatusError | None = None
    for attempt in range(max_retries):
        try:
            return _spotify_get_once(endpoint, access_token, params)
        except httpx.HTTPStatusError as err:
            last_err = err
            if err.response.status_code != 429 or attempt >= max_retries - 1:
                raise
            wait = float(err.response.headers.get("Retry-After", min(2 ** attempt, 10)))
            time.sleep(wait)
    if last_err:
        raise last_err
    raise RuntimeError("spotify_get_with_retry: unreachable")


def spotify_post_token(data: dict) -> dict:
    """
    Realiza una peticion POST al endpoint de tokens de Spotify (intercambio de codigo).

    Args:
        data (dict): Payload form-encoded para el intercambio de tokens.

    Returns:
        dict: Respuesta JSON con access_token, refresh_token, expires_in.

    Raises:
        httpx.HTTPStatusError: Si Spotify retorna un error en el intercambio.
    """
    with httpx.Client() as client:
        response = client.post(
            SPOTIFY_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()
