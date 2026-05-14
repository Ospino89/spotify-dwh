"""
filename: tracks.py (router)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router para top tracks del usuario.
             GET /top retorna tracks desde dwh.dim_tracks.
"""

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db_dependency
from app.core.security import get_current_user
from app.v1.schemas.tracks import TrackResponse
from app.v1.services.tracks_service import get_top_tracks

router = APIRouter()


@router.get("/top", response_model=list[TrackResponse], summary="Top tracks del usuario")
def top_tracks(
    limit: int = Query(50, ge=1, le=50, description="Numero de tracks a retornar"),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Retorna los top tracks almacenados en dwh.dim_tracks, ordenados por popularidad.
    Requiere JWT valido. Ejecutar el ETL primero para tener datos.

    Args:
        limit (int): Cantidad de tracks (1-50, default 50).
        current_user (str): spotify_id del usuario autenticado.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        list[TrackResponse]: Lista de tracks con sus atributos.
    """
    return get_top_tracks(conn, current_user, limit)