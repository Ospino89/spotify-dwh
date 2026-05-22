"""
filename: history_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio ETL para extraer, transformar y cargar el historial de reproducciones
             desde la Spotify API hacia dwh.fact_listening_history.
             Implementa la carga incremental con cursor Unix ms.
"""

from datetime import datetime, timezone
import psycopg2.extras
from app.core.spotify_client import spotify_get


# ---------------------------------------------------------------------------
# Cursor helper
# ---------------------------------------------------------------------------

def played_at_to_unix_ms(played_at_iso: str) -> int:
    """
    Convierte una fecha ISO 8601 con 'Z' a Unix milliseconds para el cursor de Spotify.

    Args:
        played_at_iso (str): Fecha en formato '2025-05-08T14:23:11.149Z'.

    Returns:
        int: Timestamp Unix en milisegundos, usado como parametro 'after' en Spotify API.
    """
    dt = datetime.fromisoformat(played_at_iso.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def get_last_cursor(conn, spotify_user_id: str) -> int | None:
    """
    Obtiene el cursor de la ultima ejecucion exitosa del ETL para un usuario.
    Si no hay ejecuciones previas, retorna None (primera carga sin cursor).

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_user_id (str): ID del usuario en Spotify.

    Returns:
        int | None: cursor_next_ms de la ultima ejecucion exitosa, o None si es la primera.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cursor_next_ms
            FROM dwh.etl_audit
            WHERE spotify_user_id = %s AND status = 'success'
            AND cursor_next_ms IS NOT NULL
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (spotify_user_id,),
        )
        row = cur.fetchone()
    if row and row[0]:
        return row[0] + 1  # +1 ms para excluir el último ya guardado
    return None


def get_max_played_at_ms(conn, spotify_user_id: str) -> int | None:
    """
    Obtiene el MAX(played_at) de fact_listening_history para el usuario
    y lo convierte a Unix ms. Este valor se guarda como cursor para la proxima ejecucion.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_user_id (str): ID del usuario en Spotify.

    Returns:
        int | None: MAX(played_at) como Unix ms, o None si no hay filas.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXTRACT(EPOCH FROM MAX(f.played_at)) * 1000
            FROM dwh.fact_listening_history f
            JOIN dwh.dim_users u ON u.user_id = f.user_id
            WHERE u.spotify_id = %s
            """,
            (spotify_user_id,),
        )
        row = cur.fetchone()
    return int(row[0]) if row and row[0] else None


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------
def extract_recently_played(token: str, after_ms: int | None = None) -> tuple[list[dict], int | None]:
    """
    Llama al endpoint /v1/me/player/recently-played de Spotify y retorna la lista cruda
    junto con el cursor 'after' para la proxima ejecucion.

    Args:
        token (str): Access token de Spotify (Bearer).
        after_ms (int | None): Cursor Unix ms de la ultima ejecucion. None = primera carga.

    Returns:
        tuple[list[dict], int | None]: (items, cursor_next_ms) donde cursor_next_ms
                                       es el cursor 'after' que retorna Spotify.
    """
    params = {"limit": 50}
    if after_ms is not None:
        params["after"] = after_ms

    data = spotify_get("/me/player/recently-played", token, params=params)
    items = data.get("items") or []

    cursors = data.get("cursors") or {}
    cursor_next = cursors.get("after")

    # Spotify puede devolver cursors: null si no hay novedades tras `after`
    if cursor_next is None and items:
        cursor_next = played_at_to_unix_ms(items[0]["played_at"])

    if cursor_next is None:
        return items, None

    return items, int(cursor_next)

# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_recently_played(raw_items: list[dict]) -> list[dict]:
    """
    Normaliza la lista cruda de reproducciones de Spotify al modelo de fact_listening_history.

    Args:
        raw_items (list[dict]): Lista cruda retornada por extract_recently_played.

    Returns:
        list[dict]: Lista de dicts listos para insertar en fact_listening_history.
                    Cada dict tiene: track_spotify_id, artist_spotify_id, played_at,
                    hour_of_day, day_of_week, context_type.
    """
    result = []
    for item in raw_items:
        played_at_str = item["played_at"]
        played_at_dt = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))

        result.append({
            "track_spotify_id": item["track"]["id"],
            "artist_spotify_id": item["track"]["artists"][0]["id"] if item["track"].get("artists") else None,
            "played_at": played_at_dt,
            "hour_of_day": played_at_dt.hour,
            "day_of_week": played_at_dt.strftime("%A"),
            "context_type": item.get("context", {}).get("type") if item.get("context") else "unknown",
        })
    return result


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_fact_listening_history(conn, history: list[dict], user_id: int) -> tuple[int, int]:
    """
    Inserta registros en dwh.fact_listening_history con idempotencia via ON CONFLICT DO NOTHING.
    Resuelve las FK a dim_tracks y dim_artists por spotify_id.

    Args:
        conn: Conexion activa a PostgreSQL.
        history (list[dict]): Lista de reproducciones transformadas.
        user_id (int): PK del usuario en dwh.dim_users.

    Returns:
        tuple[int, int]: (insertados, omitidos) — registros nuevos vs duplicados ignorados.
    """
    inserted = 0
    skipped = 0
    with conn.cursor() as cur:
        for item in history:
            # Resolver FK: track_id
            track_id = None
            if item.get("track_spotify_id"):
                cur.execute(
                    "SELECT track_id FROM dwh.dim_tracks WHERE spotify_id = %s",
                    (item["track_spotify_id"],),
                )
                row = cur.fetchone()
                track_id = row[0] if row else None

            # Resolver FK: artist_id
            artist_id = None
            if item.get("artist_spotify_id"):
                cur.execute(
                    "SELECT artist_id FROM dwh.dim_artists WHERE spotify_id = %s",
                    (item["artist_spotify_id"],),
                )
                row = cur.fetchone()
                artist_id = row[0] if row else None

            if track_id is None or artist_id is None:
                # No se puede insertar sin FK validas — omitir
                skipped += 1
                continue

            cur.execute(
                """
                INSERT INTO dwh.fact_listening_history
                    (user_id, track_id, artist_id, played_at, hour_of_day, day_of_week, context_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, played_at) DO NOTHING
                """,
                (
                    user_id,
                    track_id,
                    artist_id,
                    item["played_at"],
                    item["hour_of_day"],
                    item["day_of_week"],
                    item["context_type"],
                ),
            )
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
    return inserted, skipped


# ---------------------------------------------------------------------------
# Query (para el endpoint GET /v1/history/recently-played)
# ---------------------------------------------------------------------------

def get_listening_history(conn, spotify_id: str, limit: int = 50) -> list[dict]:
    """
    Consulta el historial de reproducciones del usuario desde fact_listening_history.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): spotify_id del usuario autenticado.
        limit (int): Maximo de registros a retornar (default 50).

    Returns:
        list[dict]: Lista de reproducciones ordenadas por played_at DESC.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT f.id, f.user_id, f.track_id, f.artist_id,
                   f.played_at, f.hour_of_day, f.day_of_week, f.context_type,
                   t.spotify_id as track_spotify_id,
                   a.spotify_id as artist_spotify_id
            FROM dwh.fact_listening_history f
            JOIN dwh.dim_users u  ON u.user_id  = f.user_id
            JOIN dwh.dim_tracks t ON t.track_id  = f.track_id
            JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
            WHERE u.spotify_id = %s
            ORDER BY f.played_at DESC
            LIMIT %s
            """,
            (spotify_id, limit),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_plays_by_hour(conn, spotify_id: str) -> list[int]:
    """
    Agrega reproducciones por hora sobre TODO el historial del usuario en el DWH.
    Misma logica que la pregunta analitica 1 (no limita a las ultimas N filas).

    Returns:
        list[int]: 24 enteros; indice i = cantidad de plays en la hora i (0-23).
    """
    hours = [0] * 24
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT f.hour_of_day, COUNT(*)::int AS total
            FROM dwh.fact_listening_history f
            JOIN dwh.dim_users u ON u.user_id = f.user_id
            WHERE u.spotify_id = %s
              AND f.hour_of_day IS NOT NULL
              AND f.hour_of_day >= 0
              AND f.hour_of_day < 24
            GROUP BY f.hour_of_day
            """,
            (spotify_id,),
        )
        for row in cur.fetchall():
            hours[row[0]] = row[1]
    return hours


def get_dominant_genres(conn, spotify_id: str, limit: int = 10) -> list[dict]:
    """
    Generos dominantes por reproducciones (pregunta analitica 4).
    Cuenta plays en fact_listening_history x UNNEST(genres) de dim_artists.

    Returns:
        list[dict]: [{"name": "latin", "plays": 42}, ...]
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT g.genre AS genero, COUNT(*)::int AS total
            FROM dwh.fact_listening_history f
            JOIN dwh.dim_users u ON u.user_id = f.user_id
            JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
            CROSS JOIN LATERAL UNNEST(COALESCE(a.genres, ARRAY[]::text[])) AS g(genre)
            WHERE u.spotify_id = %s
              AND g.genre IS NOT NULL
              AND TRIM(g.genre) <> ''
            GROUP BY g.genre
            ORDER BY total DESC
            LIMIT %s
            """,
            (spotify_id, limit),
        )
        rows = cur.fetchall()
    return [{"name": row[0], "plays": row[1]} for row in rows]
