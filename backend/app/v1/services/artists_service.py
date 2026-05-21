"""
filename: artists_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio ETL para extraer, transformar y cargar top artists
             desde la Spotify API hacia dwh.dim_artists.
             Tambien expone una funcion para consultar los artistas almacenados.
"""

import psycopg2.extras
from app.core.spotify_client import spotify_get


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract_top_artists(token: str) -> list[dict]:
    """
    Llama al endpoint /v1/me/top/artists de Spotify y retorna la lista cruda.

    Args:
        token (str): Access token de Spotify (Bearer).

    Returns:
        list[dict]: Lista de objetos artista en formato JSON crudo de Spotify.
    """
    data = spotify_get("/me/top/artists", token, params={"limit": 50, "time_range": "medium_term"})
    return data.get("items", [])


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_top_artists(raw_artists: list[dict]) -> list[dict]:
    """
    Normaliza la lista cruda de artistas de Spotify al modelo de dwh.dim_artists.

    Args:
        raw_artists (list[dict]): Lista cruda retornada por extract_top_artists.

    Returns:
        list[dict]: Lista de dicts listos para insertar en dim_artists.
                    Cada dict tiene: spotify_id, name, popularity, followers_count, genres.
    """
    result = []
    for item in raw_artists:
        result.append({
            "spotify_id": item["id"],
            "name": item["name"],
            "popularity": item.get("popularity"),
            "followers_count": item.get("followers", {}).get("total"),
            "genres": item.get("genres", []),
        })
    return result


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_dim_artists(conn, artists: list[dict]) -> tuple[int, int]:
    """
    Inserta o actualiza artistas en dwh.dim_artists (upsert por spotify_id).
    En conflicto, enriquece genres/popularity sin borrar datos ya cargados desde top artists.

    Args:
        conn: Conexion activa a PostgreSQL.
        artists (list[dict]): Lista de artistas transformados por transform_top_artists.

    Returns:
        tuple[int, int]: (insertados, actualizados_omitidos) — nuevos vs filas ya existentes.
    """
    inserted = 0
    skipped = 0
    with conn.cursor() as cur:
        for artist in artists:
            cur.execute(
                """
                INSERT INTO dwh.dim_artists (spotify_id, name, popularity, followers_count, genres, loaded_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (spotify_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    popularity = COALESCE(EXCLUDED.popularity, dwh.dim_artists.popularity),
                    followers_count = COALESCE(EXCLUDED.followers_count, dwh.dim_artists.followers_count),
                    genres = CASE
                        WHEN EXCLUDED.genres IS NOT NULL
                             AND cardinality(EXCLUDED.genres) > 0
                        THEN EXCLUDED.genres
                        ELSE dwh.dim_artists.genres
                    END,
                    loaded_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0) AS was_inserted
                """,
                (
                    artist["spotify_id"],
                    artist["name"],
                    artist["popularity"],
                    artist["followers_count"],
                    artist["genres"],
                ),
            )
            row = cur.fetchone()
            if row and row[0]:
                inserted += 1
            else:
                skipped += 1
    return inserted, skipped


# ---------------------------------------------------------------------------
# Query (para el endpoint GET /v1/artists/top)
# ---------------------------------------------------------------------------

def get_top_artists(conn, spotify_id: str, limit: int = 50) -> list[dict]:
    """
    Consulta los top artistas almacenados en dwh.dim_artists para un usuario.
    Nota: dim_artists no esta filtrada por usuario; retorna todos los artistas del DWH
    ordenados por popularidad.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): spotify_id del usuario autenticado (para validar acceso).
        limit (int): Maximo de artistas a retornar (default 50).

    Returns:
        list[dict]: Lista de artistas desde dim_artists.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT artist_id, spotify_id, name, popularity, followers_count, genres, loaded_at
            FROM dwh.dim_artists
            ORDER BY popularity DESC NULLS LAST
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]
