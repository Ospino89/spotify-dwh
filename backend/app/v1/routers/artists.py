"""
filename: artists.py (router)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router para top artistas del usuario.
             GET /top retorna artistas desde dwh.dim_artists.
"""

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db_dependency
from app.core.security import get_current_user
from app.v1.schemas.artists import ArtistResponse
from app.v1.services.artists_service import get_top_artists

router = APIRouter()


@router.get("/top", response_model=list[ArtistResponse], summary="Top artistas del usuario")
def top_artists(
    limit: int = Query(50, ge=1, le=50, description="Numero de artistas a retornar"),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Retorna los top artistas almacenados en dwh.dim_artists, ordenados por popularidad.
    Requiere JWT valido. Ejecutar el ETL primero para tener datos.

    Args:
        limit (int): Cantidad de artistas (1-50, default 50).
        current_user (str): spotify_id del usuario autenticado.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        list[ArtistResponse]: Lista de artistas con sus atributos.
    """
    return get_top_artists(conn, current_user, limit)