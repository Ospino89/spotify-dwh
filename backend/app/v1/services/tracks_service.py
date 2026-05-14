"""
filename: tracks_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio ETL para extraer, transformar y cargar top tracks
             desde la Spotify API hacia dwh.dim_tracks.
             Tambien expone una funcion para consultar los tracks almacenados.
"""

import psycopg2.extras
from app.core.spotify_client import spotify_get


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract_top_tracks(token: str) -> list[dict]:
    """
    Llama al endpoint /v1/me/top/tracks de Spotify y retorna la lista cruda.

    Args:
        token (str): Access token de Spotify (Bearer).

    Returns:
        list[dict]: Lista de objetos track en formato JSON crudo de Spotify.
    """
    data = spotify_get("/me/top/tracks", token, params={"limit": 50, "time_range": "medium_term"})
    return data.get("items", [])


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_top_tracks(raw_tracks: list[dict]) -> list[dict]:
    """
    Normaliza la lista cruda de tracks de Spotify al modelo de dwh.dim_tracks.

    Args:
        raw_tracks (list[dict]): Lista cruda retornada por extract_top_tracks.

    Returns:
        list[dict]: Lista de dicts listos para insertar en dim_tracks.
                    Cada dict tiene: spotify_id, name, artist_spotify_id, album_name,
                    duration_ms, popularity, explicit.
    """
    result = []
    for item in raw_tracks:
        result.append({
            "spotify_id": item["id"],
            "name": item["name"],
            "artist_spotify_id": item["artists"][0]["id"] if item.get("artists") else None,
            "album_name": item.get("album", {}).get("name"),
            "duration_ms": item.get("duration_ms"),
            "popularity": item.get("popularity"),
            "explicit": item.get("explicit", False),
        })
    return result


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_dim_tracks(conn, tracks: list[dict]) -> tuple[int, int]:
    """
    Inserta tracks en dwh.dim_tracks con idempotencia via ON CONFLICT DO NOTHING.
    Resuelve el FK a dim_artists buscando artist_id por spotify_id del artista.

    Args:
        conn: Conexion activa a PostgreSQL.
        tracks (list[dict]): Lista de tracks transformados por transform_top_tracks.

    Returns:
        tuple[int, int]: (insertados, omitidos) — conteo de registros nuevos vs ya existentes.
    """
    inserted = 0
    skipped = 0
    with conn.cursor() as cur:
        for track in tracks:
            # Resolver FK: buscar artist_id en dim_artists por spotify_id del artista
            artist_id = None
            if track.get("artist_spotify_id"):
                cur.execute(
                    "SELECT artist_id FROM dwh.dim_artists WHERE spotify_id = %s",
                    (track["artist_spotify_id"],),
                )
                row = cur.fetchone()
                artist_id = row[0] if row else None

            cur.execute(
                """
                INSERT INTO dwh.dim_tracks
                    (spotify_id, name, artist_id, album_name, duration_ms, popularity, explicit, loaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (spotify_id) DO NOTHING
                """,
                (
                    track["spotify_id"],
                    track["name"],
                    artist_id,
                    track["album_name"],
                    track["duration_ms"],
                    track["popularity"],
                    track["explicit"],
                ),
            )
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
    return inserted, skipped


# ---------------------------------------------------------------------------
# Query (para el endpoint GET /v1/tracks/top)
# ---------------------------------------------------------------------------

def get_top_tracks(conn, spotify_id: str, limit: int = 50) -> list[dict]:
    """
    Consulta los top tracks almacenados en dwh.dim_tracks.
    Ordenados por popularidad descendente.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): spotify_id del usuario autenticado (para validar acceso).
        limit (int): Maximo de tracks a retornar (default 50).

    Returns:
        list[dict]: Lista de tracks desde dim_tracks.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT track_id, spotify_id, name, artist_id, album_name,
                   duration_ms, popularity, explicit, loaded_at
            FROM dwh.dim_tracks
            ORDER BY popularity DESC NULLS LAST
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]
