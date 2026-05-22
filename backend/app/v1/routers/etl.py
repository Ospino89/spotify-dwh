"""
filename: etl.py (router)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router para disparar y consultar el pipeline ETL.
             POST /run ejecuta el pipeline completo (extract->transform->load).
             GET /status retorna las ultimas ejecuciones del etl_audit.
"""

from fastapi import APIRouter, Depends

from app.core.database import get_db_dependency
from app.core.security import get_current_user
from app.v1.services.etl_service import get_etl_status, repair_artists_popularity, run_etl

router = APIRouter()


@router.post("/run", summary="Ejecuta el pipeline ETL completo")
def trigger_etl(
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Dispara el pipeline ETL completo para el usuario autenticado:
    extrae top artists, top tracks y recently played desde Spotify,
    los transforma y los carga en el DWH de forma incremental.
    Registra la ejecucion en dwh.etl_audit con metricas.

    Args:
        current_user (str): spotify_id del usuario autenticado.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        dict: Metricas de la ejecucion (registros insertados, omitidos, duracion).
    """
    return run_etl(conn, current_user)


@router.post(
    "/repair-artists",
    summary="Rellena popularity NULL en dim_artists",
    include_in_schema=False,
)
def repair_artists(
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Repara popularity y genres sin extract completo.
    Genres: MusicBrainz si Spotify devuelve genres vacios (~45s, hasta 40 artistas).
    """
    return repair_artists_popularity(conn, current_user)


@router.get("/status", summary="Estado de las ultimas ejecuciones del ETL")
def etl_status(
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db_dependency),
):
    """
    Retorna las ultimas 20 ejecuciones del ETL para el usuario autenticado
    desde dwh.etl_audit, ordenadas por fecha descendente.

    Args:
        current_user (str): spotify_id del usuario autenticado.
        conn: Conexion a PostgreSQL inyectada por FastAPI.

    Returns:
        list[dict]: Lista de ejecuciones con status, metricas y timestamps.
    """
    return get_etl_status(conn, current_user)