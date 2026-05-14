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
from app.v1.services.history_service import get_listening_history

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