"""
filename: tracks_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio ETL para extraer, transformar y cargar top tracks
             desde la Spotify API hacia dwh.dim_tracks.
             Tambien expone una funcion para consultar los tracks almacenados.
"""

import httpx
import psycopg2.extras
from app.core.spotify_client import spotify_get

_TRACKS_BATCH_SIZE = 20


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


def _fetch_single_track_popularity(token: str, track_id: str) -> int | None:
    """GET /v1/tracks/{id} — fallback cuando el batch devuelve 403."""
    try:
        data = spotify_get(f"/tracks/{track_id}", token)
        return data.get("popularity")
    except httpx.HTTPStatusError:
        return None


def _fetch_popularity_by_track_ids(token: str, track_ids: list[str]) -> dict[str, int]:
    """
    Intenta obtener popularity desde GET /v1/tracks.
    Si Spotify responde 403 (comun en apps en modo desarrollo), no rompe el ETL.
    """
    popularity_by_id: dict[str, int] = {}
    unique_ids = list(dict.fromkeys(track_ids))

    for i in range(0, len(unique_ids), _TRACKS_BATCH_SIZE):
        chunk = unique_ids[i : i + _TRACKS_BATCH_SIZE]
        try:
            data = spotify_get("/tracks", token, params={"ids": ",".join(chunk)})
            for track in data.get("tracks") or []:
                if track and track.get("id") and track.get("popularity") is not None:
                    popularity_by_id[track["id"]] = track["popularity"]
        except httpx.HTTPStatusError:
            for tid in chunk:
                if tid not in popularity_by_id:
                    pop = _fetch_single_track_popularity(token, tid)
                    if pop is not None:
                        popularity_by_id[tid] = pop

    return popularity_by_id


def _apply_rank_popularity_fallback(raw_tracks: list[dict]) -> list[dict]:
    """
    Si la API de catalogo no esta disponible, deriva popularity del ranking del top 50.
    Posicion 1 -> 100, posicion 2 -> 98, etc. (solo para /me/top/tracks ordenado).
    """
    enriched = []
    for index, item in enumerate(raw_tracks):
        copy = dict(item)
        if copy.get("popularity") is None:
            copy["popularity"] = max(1, 100 - index * 2)
        enriched.append(copy)
    return enriched


def enrich_tracks_with_popularity(
    token: str,
    raw_tracks: list[dict],
    *,
    use_rank_fallback: bool = False,
) -> list[dict]:
    """
    Completa popularity: primero API /tracks, luego (opcional) ranking del top 50.

    Args:
        token (str): Access token de Spotify.
        raw_tracks (list[dict]): Tracks crudos (top o recently-played).
        use_rank_fallback (bool): True para top tracks si la API de catalogo falla.

    Returns:
        list[dict]: Tracks con popularity cuando fue posible obtenerla.
    """
    if not raw_tracks:
        return raw_tracks

    track_ids = [t["id"] for t in raw_tracks if t.get("id")]
    popularity_by_id = _fetch_popularity_by_track_ids(token, track_ids)

    enriched = []
    for item in raw_tracks:
        copy = dict(item)
        track_id = copy.get("id")
        if copy.get("popularity") is None and track_id and track_id in popularity_by_id:
            copy["popularity"] = popularity_by_id[track_id]
        enriched.append(copy)

    if use_rank_fallback and any(t.get("popularity") is None for t in enriched):
        return _apply_rank_popularity_fallback(enriched)

    return enriched


def backfill_popularity_from_listening_history(conn) -> int:
    """
    Rellena popularity NULL usando reproducciones en fact_listening_history.
    Proxy: numero de plays (cap 100) cuando Spotify /tracks no esta autorizado.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE dwh.dim_tracks t
            SET popularity = LEAST(100, agg.plays),
                loaded_at = CURRENT_TIMESTAMP
            FROM (
                SELECT f.track_id, COUNT(*)::int AS plays
                FROM dwh.fact_listening_history f
                GROUP BY f.track_id
            ) agg
            WHERE t.track_id = agg.track_id
              AND t.popularity IS NULL
              AND agg.plays > 0
            """
        )
        updated = cur.rowcount
    return updated


def backfill_dim_tracks_popularity(conn, token: str, limit: int = 40) -> int:
    """
    Intenta reparar popularity NULL via API (pocos ids) y luego via historial de plays.

    Args:
        conn: Conexion activa a PostgreSQL.
        token (str): Access token de Spotify.
        limit (int): Maximo de ids a consultar en Spotify por corrida.

    Returns:
        int: Total de filas actualizadas (API + historial).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT spotify_id FROM dwh.dim_tracks
            WHERE popularity IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        spotify_ids = [row[0] for row in cur.fetchall()]

    api_updated = 0
    if spotify_ids:
        popularity_by_id = _fetch_popularity_by_track_ids(token, spotify_ids)
        with conn.cursor() as cur:
            for sid, popularity in popularity_by_id.items():
                cur.execute(
                    """
                    UPDATE dwh.dim_tracks
                    SET popularity = %s, loaded_at = CURRENT_TIMESTAMP
                    WHERE spotify_id = %s AND popularity IS NULL
                    """,
                    (popularity, sid),
                )
                api_updated += cur.rowcount

    history_updated = backfill_popularity_from_listening_history(conn)
    return api_updated + history_updated


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
    Inserta o actualiza tracks en dwh.dim_tracks (upsert por spotify_id).
    Resuelve el FK a dim_artists y conserva popularity si el historial no la trae.

    Args:
        conn: Conexion activa a PostgreSQL.
        tracks (list[dict]): Lista de tracks transformados por transform_top_tracks.

    Returns:
        tuple[int, int]: (insertados, actualizados_omitidos) — nuevos vs filas ya existentes.
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
                ON CONFLICT (spotify_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    artist_id = COALESCE(EXCLUDED.artist_id, dwh.dim_tracks.artist_id),
                    album_name = COALESCE(EXCLUDED.album_name, dwh.dim_tracks.album_name),
                    duration_ms = COALESCE(EXCLUDED.duration_ms, dwh.dim_tracks.duration_ms),
                    popularity = CASE
                        WHEN EXCLUDED.popularity IS NOT NULL
                        THEN EXCLUDED.popularity
                        ELSE dwh.dim_tracks.popularity
                    END,
                    explicit = EXCLUDED.explicit,
                    loaded_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0) AS was_inserted
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
            row = cur.fetchone()
            if row and row[0]:
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
