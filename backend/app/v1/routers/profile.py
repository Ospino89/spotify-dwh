"""
filename: profile.py (router)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router para el perfil del usuario autenticado.
             GET /me retorna los datos del usuario desde dwh.dim_users.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db_dependency
from app.core.security import get_current_user
from app.v1.schemas.profile import ProfileResponse
from app.v1.services.profile_service import get_user_profile

router = APIRouter()


@router.get("/me", response_model=ProfileResponse, summary="Perfil del usuario autenticado")
def get_my_profile(
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Retorna el perfil del usuario autenticado desde dwh.dim_users.
    Requiere JWT valido en el header Authorization: Bearer <token>.

    Args:
        current_user (str): spotify_id extraido del JWT por get_current_user.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        ProfileResponse: Datos del usuario (sin tokens de Spotify).

    Raises:
        HTTPException 404: Si el usuario no existe en dim_users
                           (nunca completó el flujo de login).
    """
    profile = get_user_profile(conn, current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado. Completa el flujo de login primero.",
        )
    return profile