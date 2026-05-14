"""
filename: security.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Logica de seguridad: generacion y validacion de JWT propios de la app,
             y el dependency de FastAPI para proteger rutas autenticadas.
"""

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings

bearer_scheme = HTTPBearer()


def create_access_token(spotify_id: str) -> str:
    """
    Genera un JWT firmado con el spotify_id del usuario como 'sub'.

    Args:
        spotify_id (str): Identificador unico del usuario en Spotify.

    Returns:
        str: JWT firmado, valido por jwt_expire_hours horas (definido en Settings).
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "sub": spotify_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Dependency de FastAPI. Valida el JWT en el header Authorization y retorna el spotify_id.
    Agregar a cualquier endpoint protegido con: current_user: str = Depends(get_current_user)

    Args:
        credentials (HTTPAuthorizationCredentials): Header Bearer extraido automaticamente.

    Returns:
        str: spotify_id del usuario autenticado (campo 'sub' del JWT).

    Raises:
        HTTPException 401: Si el token falta, es invalido o expiró.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        ) 
        spotify_id: str = payload.get("sub")
        if spotify_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: falta el campo 'sub'",
            )
        return spotify_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        )
