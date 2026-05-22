"""
filename: history.py (router)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router para historial de reproducciones del usuario.
             GET /recently-played retorna filas desde dwh.fact_listening_history.
"""

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db_dependency
from app.core.security import get_current_user
from app.v1.services.history_service import (
    get_dominant_genres,
    get_listening_history,
    get_plays_by_hour,
)

router = APIRouter()


@router.get("/recently-played", summary="Historial de reproducciones recientes")
def recently_played(
    limit: int = Query(50, ge=1, le=50, description="Numero de reproducciones a retornar"),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Retorna el historial de reproducciones del usuario desde fact_listening_history,
    ordenado por played_at descendente (mas reciente primero).
    Requiere JWT valido. Ejecutar el ETL primero para tener datos.

    Args:
        limit (int): Cantidad de reproducciones (1-50, default 50).
        current_user (str): spotify_id del usuario autenticado.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        list[dict]: Lista de reproducciones con track, artista, fecha y contexto.
    """
    return get_listening_history(conn, current_user, limit)


@router.get(
    "/plays-by-hour",
    summary="Reproducciones por hora (todo el DWH)",
    response_model=list[int],
    include_in_schema=False,
)
def plays_by_hour(
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Retorna un array de 24 posiciones con el conteo de plays por hora del dia,
    agregado sobre fact_listening_history completo del usuario.
    """
    return get_plays_by_hour(conn, current_user)


@router.get(
    "/dominant-genres",
    summary="Generos dominantes por reproducciones (DWH)",
    include_in_schema=False,
)
def dominant_genres(
    limit: int = Query(10, ge=1, le=50),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Agrega plays del historial del usuario por genero del artista (UNNEST genres).
    Alineado con la pregunta analitica 4 del DWH.
    """
    return get_dominant_genres(conn, current_user, limit)