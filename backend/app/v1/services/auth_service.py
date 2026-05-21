"""
filename: auth_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio de autenticacion. Implementa el flujo completo OAuth 2.0 con PKCE:
             generacion de verifier/challenge, intercambio del code por tokens de Spotify,
             renovacion de access_token y emision del JWT propio de la app.
"""

import base64
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras

from app.core.config import settings
from app.core.security import create_access_token
from app.core.spotify_client import SPOTIFY_AUTH_URL, spotify_post_token


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

def generate_pkce_pair() -> tuple[str, str]:
    """
    Genera un par (code_verifier, code_challenge) para el flujo PKCE.

    Returns:
        tuple[str, str]: (code_verifier, code_challenge). El verifier se guarda
                         en pkce_sessions; el challenge se envia a Spotify.
    """
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def generate_state() -> str:
    """
    Genera un state aleatorio para proteger contra CSRF en el flujo OAuth.

    Returns:
        str: UUID v4 como string, usado como parametro 'state' en la URL de Spotify.
    """
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# PKCE session persistence
# ---------------------------------------------------------------------------

def save_pkce_session(conn, state: str, verifier: str) -> None:
    """
    Guarda el par (state, verifier) en public.pkce_sessions para recuperarlo en el callback.

    Args:
        conn: Conexion activa a PostgreSQL.
        state (str): UUID aleatorio que identifica la sesion OAuth.
        verifier (str): code_verifier necesario para completar el intercambio PKCE.

    Returns:
        None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.pkce_sessions (state, verifier)
            VALUES (%s, %s)
            ON CONFLICT (state) DO NOTHING
            """,
            (state, verifier),
        )


def get_pkce_session(conn, state: str) -> dict | None:
    """
    Recupera y elimina la sesion PKCE asociada al state recibido en el callback.

    Args:
        conn: Conexion activa a PostgreSQL.
        state (str): Valor del parametro 'state' recibido de Spotify en el callback.

    Returns:
        dict | None: {'state': str, 'verifier': str} si existe, None si no.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "DELETE FROM public.pkce_sessions WHERE state = %s RETURNING state, verifier",
            (state,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Spotify token exchange
# ---------------------------------------------------------------------------

def exchange_code_for_tokens(code: str, verifier: str) -> dict:
    """
    Intercambia el authorization code de Spotify por access_token y refresh_token usando PKCE.

    Args:
        code (str): Codigo de autorizacion recibido de Spotify en el callback.
        verifier (str): code_verifier original generado en /auth/login.

    Returns:
        dict: Respuesta de Spotify con access_token, refresh_token y expires_in.

    Raises:
        httpx.HTTPStatusError: Si Spotify rechaza el intercambio.
    """
    return spotify_post_token({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.spotify_redirect_uri,
        "client_id": settings.spotify_client_id.get_secret_value(),
        "code_verifier": verifier,
    })


def refresh_spotify_token(refresh_token: str) -> dict:
    """
    Renueva el access_token de Spotify usando el refresh_token almacenado.

    Args:
        refresh_token (str): Token de renovacion guardado en dim_users.

    Returns:
        dict: Respuesta de Spotify con el nuevo access_token y expires_in.

    Raises:
        httpx.HTTPStatusError: Si Spotify rechaza la renovacion.
    """
    return spotify_post_token({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.spotify_client_id.get_secret_value(),
    })


# ---------------------------------------------------------------------------
# User upsert and token management
# ---------------------------------------------------------------------------

def upsert_user_with_tokens(conn, profile: dict, token_data: dict) -> str:
    """
    Inserta o actualiza el usuario en dwh.dim_users con sus tokens de Spotify.
    Retorna el spotify_id para emitir el JWT propio de la app.

    Args:
        conn: Conexion activa a PostgreSQL.
        profile (dict): Perfil del usuario desde GET /v1/me de Spotify.
        token_data (dict): Tokens de Spotify (access_token, refresh_token, expires_in).

    Returns:
        str: spotify_id del usuario (campo 'id' del perfil de Spotify).
    """
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dwh.dim_users (
                spotify_id, display_name, email, country, followers, product,
                spotify_access_token, spotify_refresh_token, token_expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (spotify_id) DO UPDATE SET
                display_name          = EXCLUDED.display_name,
                email                 = EXCLUDED.email,
                country               = EXCLUDED.country,
                followers             = EXCLUDED.followers,
                product               = EXCLUDED.product,
                spotify_access_token  = EXCLUDED.spotify_access_token,
                spotify_refresh_token = COALESCE(EXCLUDED.spotify_refresh_token, dwh.dim_users.spotify_refresh_token),
                token_expires_at      = EXCLUDED.token_expires_at
            """,
            (
                profile.get("id"),
                profile.get("display_name"),
                profile.get("email"),
                profile.get("country"),
                profile.get("followers", {}).get("total"),
                profile.get("product"),
                token_data.get("access_token"),
                token_data.get("refresh_token"),
                expires_at,
            ),
        )
    return profile["id"]


def get_valid_spotify_token(conn, spotify_id: str) -> str:
    """
    Retorna un access_token de Spotify valido para el usuario.
    Si el token esta por expirar (menos de 5 minutos), lo renueva automaticamente.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): ID del usuario en Spotify.

    Returns:
        str: access_token de Spotify vigente.

    Raises:
        ValueError: Si el usuario no existe en la DB.
        httpx.HTTPStatusError: Si falla la renovacion del token.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT spotify_access_token, spotify_refresh_token, token_expires_at
            FROM dwh.dim_users
            WHERE spotify_id = %s
            """,
            (spotify_id,),
        )
        row = cur.fetchone()

    if not row:
        raise ValueError(f"Usuario {spotify_id} no encontrado en dim_users")

    # Renovar si expira en menos de 5 minutos
    expires_at = row["token_expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at - datetime.now(timezone.utc) < timedelta(minutes=5):
        new_tokens = refresh_spotify_token(row["spotify_refresh_token"])
        new_expires = datetime.now(timezone.utc) + timedelta(seconds=new_tokens.get("expires_in", 3600))
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE dwh.dim_users
                SET spotify_access_token = %s, token_expires_at = %s
                WHERE spotify_id = %s
                """,
                (new_tokens["access_token"], new_expires, spotify_id),
            )
        conn.commit()
        return new_tokens["access_token"]

    return row["spotify_access_token"]


# ---------------------------------------------------------------------------
# Spotify Authorization URL builder
# ---------------------------------------------------------------------------

def build_spotify_auth_url(state: str, challenge: str) -> str:
    """
    Construye la URL de autorizacion de Spotify con todos los parametros PKCE.

    Args:
        state (str): UUID aleatorio para proteccion CSRF.
        challenge (str): code_challenge derivado del code_verifier via SHA-256.

    Returns:
        str: URL completa para redirigir al usuario a Spotify.
    """
    scopes = "user-read-private user-read-email user-top-read user-read-recently-played"
    params = (
        f"response_type=code"
        f"&client_id={settings.spotify_client_id.get_secret_value()}"
        f"&redirect_uri={settings.spotify_redirect_uri}"
        f"&scope={scopes.replace(' ', '%20')}"
        f"&state={state}"
        f"&code_challenge_method=S256"
        f"&code_challenge={challenge}"
    )
    return f"{SPOTIFY_AUTH_URL}?{params}"