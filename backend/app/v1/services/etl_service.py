"""
filename: etl_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Orquestador del pipeline ETL completo.
             Coordina extract -> transform -> load para artists, tracks e history.
             Registra cada ejecucion en dwh.etl_audit con metricas y cursor incremental.
"""

import time
from datetime import datetime, timezone

import psycopg2.extras

from app.v1.services.auth_service import get_valid_spotify_token
from app.v1.services.artists_service import (
    extract_top_artists,
    transform_top_artists,
    load_dim_artists,
)
from app.v1.services.tracks_service import (
    extract_top_tracks,
    transform_top_tracks,
    load_dim_tracks,
)
from app.v1.services.history_service import (
    extract_recently_played,
    transform_recently_played,
    load_fact_listening_history,
    get_last_cursor,
    get_max_played_at_ms,
)


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------

def insert_audit_start(conn, spotify_user_id: str, cursor_after_ms: int | None) -> int:
    """
    Inserta una fila en dwh.etl_audit con status='running' al inicio del pipeline.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_user_id (str): ID del usuario en Spotify.
        cursor_after_ms (int | None): Cursor usado en esta ejecucion (None = primera carga).

    Returns:
        int: audit_id de la fila recien creada.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dwh.etl_audit
                (spotify_user_id, status, started_at, cursor_after_ms)
            VALUES (%s, 'running', CURRENT_TIMESTAMP, %s)
            RETURNING audit_id
            """,
            (spotify_user_id, cursor_after_ms),
        )
        audit_id = cur.fetchone()[0]
    conn.commit()
    return audit_id


def update_audit_success(conn, audit_id: int, metrics: dict, cursor_next_ms: int | None) -> None:
    """
    Actualiza la fila de auditoria con status='success' y las metricas de la ejecucion.

    Args:
        conn: Conexion activa a PostgreSQL.
        audit_id (int): PK de la fila en etl_audit.
        metrics (dict): Conteo de registros por tabla (artists_inserted, tracks_inserted, etc.).
        cursor_next_ms (int | None): MAX(played_at) convertido a ms para la proxima ejecucion.

    Returns:
        None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE dwh.etl_audit SET
                status               = 'success',
                finished_at          = CURRENT_TIMESTAMP,
                duration_ms          = %s,
                artists_inserted     = %s,
                artists_skipped      = %s,
                tracks_inserted      = %s,
                tracks_skipped       = %s,
                history_inserted     = %s,
                history_skipped      = %s,
                cursor_next_ms       = %s
            WHERE audit_id = %s
            """,
            (
                metrics.get("duration_ms"),
                metrics.get("artists_inserted", 0),
                metrics.get("artists_skipped", 0),
                metrics.get("tracks_inserted", 0),
                metrics.get("tracks_skipped", 0),
                metrics.get("history_inserted", 0),
                metrics.get("history_skipped", 0),
                cursor_next_ms,
                audit_id,
            ),
        )
    conn.commit()


def update_audit_error(conn, audit_id: int, error: str, duration_ms: int) -> None:
    """
    Actualiza la fila de auditoria con status='error' y el mensaje de la excepcion.

    Args:
        conn: Conexion activa a PostgreSQL.
        audit_id (int): PK de la fila en etl_audit.
        error (str): Mensaje de la excepcion capturada.
        duration_ms (int): Tiempo transcurrido hasta el fallo en milisegundos.

    Returns:
        None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE dwh.etl_audit SET
                status      = 'error',
                finished_at = CURRENT_TIMESTAMP,
                duration_ms = %s,
                error_msg   = %s
            WHERE audit_id = %s
            """,
            (duration_ms, str(error)[:1000], audit_id),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def run_etl(conn, spotify_id: str) -> dict:
    """
    Ejecuta el pipeline ETL completo para el usuario autenticado.
    Fases: (1) obtener token valido, (2) extract, (3) transform, (4) load, (5) audit.
    Usa carga incremental: solo trae reproducciones posteriores al ultimo cursor guardado.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): ID del usuario en Spotify (del JWT).

    Returns:
        dict: Metricas de la ejecucion: registros insertados/omitidos por tabla,
              duracion en ms, cursor utilizado y proximo cursor.

    Raises:
        Exception: Cualquier error queda registrado en etl_audit con status='error'.
    """
    start_ms = int(time.time() * 1000)

    # Obtener user_id para las cargas
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM dwh.dim_users WHERE spotify_id = %s", (spotify_id,))
        row = cur.fetchone()
    user_id = row[0] if row else None

    # Obtener cursor de la ultima ejecucion exitosa
    cursor_after_ms = get_last_cursor(conn, spotify_id)

    # Iniciar registro de auditoria
    audit_id = insert_audit_start(conn, spotify_id, cursor_after_ms)

    try:
        # 1. Token valido (renueva si es necesario)
        token = get_valid_spotify_token(conn, spotify_id)

        # 2. EXTRACT
        raw_artists = extract_top_artists(token)
        raw_tracks  = extract_top_tracks(token)
        raw_history = extract_recently_played(token, after_ms=cursor_after_ms)

        # 3. TRANSFORM
        artists = transform_top_artists(raw_artists)
        tracks  = transform_top_tracks(raw_tracks)
        history = transform_recently_played(raw_history)

        # 4. LOAD (orden: artists -> tracks -> history para respetar FK)
        artists_in, artists_sk = load_dim_artists(conn, artists)
        tracks_in,  tracks_sk  = load_dim_tracks(conn, tracks)

        history_in, history_sk = (0, 0)
        if user_id:
            history_in, history_sk = load_fact_listening_history(conn, history, user_id)

        conn.commit()

        # 5. Calcular cursor para la proxima ejecucion
        cursor_next_ms = get_max_played_at_ms(conn, spotify_id)

        duration_ms = int(time.time() * 1000) - start_ms

        metrics = {
            "duration_ms":       duration_ms,
            "artists_inserted":  artists_in,
            "artists_skipped":   artists_sk,
            "tracks_inserted":   tracks_in,
            "tracks_skipped":    tracks_sk,
            "history_inserted":  history_in,
            "history_skipped":   history_sk,
        }

        update_audit_success(conn, audit_id, metrics, cursor_next_ms)

        return {
            "status":          "success",
            "cursor_after_ms": cursor_after_ms,
            "cursor_next_ms":  cursor_next_ms,
            **metrics,
        }

    except Exception as exc:
        duration_ms = int(time.time() * 1000) - start_ms
        update_audit_error(conn, audit_id, str(exc), duration_ms)
        raise


# ---------------------------------------------------------------------------
# Query de estado
# ---------------------------------------------------------------------------

def get_etl_status(conn, spotify_id: str) -> list[dict]:
    """
    Retorna las ultimas 20 ejecuciones del ETL para el usuario desde dwh.etl_audit.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): ID del usuario en Spotify.

    Returns:
        list[dict]: Lista de ejecuciones ordenadas por started_at DESC,
                    con status, metricas, cursor y duracion.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT audit_id, status, started_at, finished_at, duration_ms,
                   artists_inserted, artists_skipped,
                   tracks_inserted,  tracks_skipped,
                   history_inserted, history_skipped,
                   cursor_after_ms, cursor_next_ms, error_msg
            FROM dwh.etl_audit
            WHERE spotify_user_id = %s
            ORDER BY started_at DESC
            LIMIT 20
            """,
            (spotify_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]
