"""
filename: auth.py (router)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router de autenticacion OAuth 2.0 con PKCE.
             Implementa GET /login (genera URL de Spotify) y
             GET /callback (intercambia code por tokens y emite JWT propio).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.database import get_db_dependency
from app.core.security import create_access_token
from app.core.spotify_client import spotify_get
from app.v1.services.auth_service import (
    build_spotify_auth_url,
    exchange_code_for_tokens,
    generate_pkce_pair,
    generate_state,
    get_pkce_session,
    save_pkce_session,
    upsert_user_with_tokens,
)

router = APIRouter()


@router.get("/login", summary="Inicia el flujo OAuth PKCE con Spotify")
def login(conn=Depends(get_db_dependency)):
    """
    Genera un par PKCE (verifier + challenge), guarda el state en pkce_sessions
    y redirige al usuario a la pantalla de autorizacion de Spotify.

    Args:
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        RedirectResponse: Redireccion 302 a la URL de autorizacion de Spotify.
    """
    state = generate_state()
    verifier, challenge = generate_pkce_pair()

    save_pkce_session(conn, state, verifier)

    url = build_spotify_auth_url(state, challenge)
    return RedirectResponse(url, status_code=302)


@router.get("/callback", summary="Callback de Spotify: intercambia code por JWT propio")
def callback(
    code: str = Query(..., description="Authorization code recibido de Spotify"),
    state: str = Query(..., description="State para validar la sesion PKCE"),
    conn=Depends(get_db_dependency),
):
    """
    Recibe el code y el state de Spotify tras la autorizacion del usuario.
    Valida el state contra pkce_sessions, intercambia el code por tokens,
    persiste el usuario en dim_users y redirige al frontend con el JWT propio.

    Args:
        code (str): Authorization code de Spotify (parametro de query).
        state (str): State UUID para validar que la sesion PKCE es legitima.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        RedirectResponse: Redireccion al frontend con ?token=<jwt> en la URL.

    Raises:
        HTTPException 401: Si el state no existe o ya fue consumido.
        HTTPException 502: Si Spotify rechaza el intercambio de tokens.
    """
    # 1. Validar state y recuperar verifier
    session = get_pkce_session(conn, state)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="State invalido o sesion PKCE expirada",
        )

    # 2. Intercambiar code por tokens de Spotify
    try:
        token_data = exchange_code_for_tokens(code, session["verifier"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al intercambiar tokens con Spotify: {exc}",
        )

    # 3. Obtener perfil del usuario desde Spotify
    try:
        profile = spotify_get("/me", token_data["access_token"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al obtener perfil de Spotify: {exc}",
        )

    # 4. Upsert en dim_users y obtener spotify_id
    spotify_id = upsert_user_with_tokens(conn, profile, token_data)

    # 5. Emitir JWT propio de la app
    jwt_token = create_access_token(spotify_id)

    # 6. Redirigir al frontend con el token
    from app.core.config import settings
    return RedirectResponse(
        url=f"{settings.frontend_url}?token={jwt_token}",
        status_code=302,
    )