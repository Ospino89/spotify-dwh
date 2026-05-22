"""
filename: artists_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio ETL para extraer, transformar y cargar top artists
             desde la Spotify API hacia dwh.dim_artists.
             Tambien expone una funcion para consultar los artistas almacenados.
"""

import time
import httpx
import psycopg2.extras
from app.core.spotify_client import spotify_get, spotify_get_with_retry
from app.v1.services.genre_fallback_service import backfill_genres_via_musicbrainz

_ARTISTS_BATCH_SIZE = 20
_CATALOG_FORBIDDEN_LOGGED = False
_SEARCH_DELAY_SECONDS = 0.35
_SEARCH_GENRE_LIMIT = 25


def _normalize_genres(item: dict) -> list[str]:
    """Extrae genres del objeto artista de Spotify (lista de strings no vacia)."""
    raw = item.get("genres")
    if not isinstance(raw, list):
        return []
    return [str(g).strip() for g in raw if g and str(g).strip()]


def _followers_total(item: dict) -> int | None:
    """Spotify a veces devuelve followers: null en lugar de omitir el campo."""
    followers = item.get("followers")
    if isinstance(followers, dict):
        return followers.get("total")
    return None


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


def _fetch_artists_by_ids(token: str, artist_ids: list[str]) -> dict[str, dict]:
    """
    GET /v1/artists (catalogo). En modo Development suele devolver 403:
    no hace llamadas uno a uno para evitar 429 y bloqueos del ETL.
    """
    global _CATALOG_FORBIDDEN_LOGGED
    result: dict[str, dict] = {}
    unique_ids = list(dict.fromkeys(artist_ids))
    if not unique_ids:
        return result

    for i in range(0, len(unique_ids), _ARTISTS_BATCH_SIZE):
        chunk = unique_ids[i : i + _ARTISTS_BATCH_SIZE]
        try:
            data = spotify_get_with_retry(
                "/artists", token, params={"ids": ",".join(chunk)}
            )
            for artist in data.get("artists") or []:
                if artist and artist.get("id"):
                    result[artist["id"]] = artist
        except httpx.HTTPStatusError as batch_err:
            status = batch_err.response.status_code
            if status == 403:
                if not _CATALOG_FORBIDDEN_LOGGED:
                    print(
                        "[ETL INFO] Catalogo /artists no disponible (403). "
                        "Se usan /me/top/artists, historial de plays y ranking local."
                    )
                    _CATALOG_FORBIDDEN_LOGGED = True
                break
            if status == 429:
                print("[ETL WARNING] Rate limit en /artists — se omite el resto del catalogo.")
                break
            print(
                f"[ETL WARNING] GET /artists batch falló ({status}): "
                f"{batch_err.response.text[:200]}"
            )
    return result


def _apply_known_artist_metadata(item: dict, known: dict | None) -> dict:
    """Copia genres/popularity/followers desde el mapa del top 50 (sin API de catalogo)."""
    copy = dict(item)
    artist_id = copy.get("id")
    if not artist_id or not known:
        return copy
    meta = known.get(artist_id)
    if not meta:
        return copy
    if copy.get("popularity") is None and meta.get("popularity") is not None:
        copy["popularity"] = meta.get("popularity")
    meta_genres = _normalize_genres(meta)
    if not _normalize_genres(copy) and meta_genres:
        copy["genres"] = meta_genres
    if not copy.get("followers") and meta.get("followers"):
        copy["followers"] = meta.get("followers")
    return copy


def _needs_catalog_enrich(item: dict) -> bool:
    """Artistas del historial traen solo id/name; los del top ya vienen completos."""
    if not item.get("id"):
        return False
    has_genres = bool(item.get("genres"))
    has_popularity = item.get("popularity") is not None
    has_followers = isinstance(item.get("followers"), dict)
    return not (has_genres or has_popularity or has_followers)


def enrich_artists_with_metadata(
    token: str,
    raw_artists: list[dict],
    *,
    known_artists_by_id: dict[str, dict] | None = None,
    use_catalog_api: bool = False,
) -> list[dict]:
    """
    Completa datos de artistas del historial.
    Por defecto NO llama a /artists (403/429 en Development); usa el top 50 en memoria.
    """
    if not raw_artists:
        return raw_artists

    enriched = [_apply_known_artist_metadata(item, known_artists_by_id) for item in raw_artists]

    if not use_catalog_api:
        still_missing = sum(1 for a in enriched if _needs_catalog_enrich(a))
        if still_missing:
            print(
                f"[ETL INFO] {still_missing} artistas del historial sin metadata de catalogo "
                "(se completan con top/plays/backfill)."
            )
        return enriched

    missing_ids = [a["id"] for a in enriched if _needs_catalog_enrich(a)]
    if not missing_ids:
        return enriched

    metadata_by_id = _fetch_artists_by_ids(token, missing_ids)
    result = []
    for item in enriched:
        copy = dict(item)
        artist_id = copy.get("id")
        if artist_id and artist_id in metadata_by_id:
            meta = metadata_by_id[artist_id]
            if copy.get("popularity") is None:
                copy["popularity"] = meta.get("popularity")
            if not copy.get("genres"):
                copy["genres"] = meta.get("genres") or []
            if not copy.get("followers"):
                copy["followers"] = meta.get("followers")
        result.append(copy)
    return result


def backfill_artist_popularity_from_plays(conn) -> int:
    """
    Rellena popularity NULL usando reproducciones en fact_listening_history.
    No depende de la API de catalogo de Spotify (evita 403 en /artists).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE dwh.dim_artists a
            SET popularity = LEAST(100, agg.plays),
                loaded_at = CURRENT_TIMESTAMP
            FROM (
                SELECT f.artist_id, COUNT(*)::int AS plays
                FROM dwh.fact_listening_history f
                GROUP BY f.artist_id
            ) agg
            WHERE a.artist_id = agg.artist_id
              AND a.popularity IS NULL
              AND agg.plays > 0
            """
        )
        updated = cur.rowcount
    return updated


def backfill_artist_popularity_fallback_rank(conn) -> int:
    """
    Ultimo recurso: asigna popularity por orden de carga cuando no hay plays ni API.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH ranked AS (
                SELECT artist_id,
                       ROW_NUMBER() OVER (ORDER BY loaded_at DESC NULLS LAST, name) AS rn
                FROM dwh.dim_artists
                WHERE popularity IS NULL
            )
            UPDATE dwh.dim_artists a
            SET popularity = GREATEST(1, 100 - (ranked.rn - 1) * 2),
                loaded_at = CURRENT_TIMESTAMP
            FROM ranked
            WHERE a.artist_id = ranked.artist_id
            """
        )
        return cur.rowcount


def _fetch_genres_via_search(token: str, artist_name: str, spotify_id: str) -> list[str]:
    """
    Fallback: GET /search?type=artist suele funcionar cuando /artists devuelve 403.
    """
    if not artist_name or not spotify_id:
        return []
    try:
        data = spotify_get_with_retry(
            "/search",
            token,
            params={"q": artist_name, "type": "artist", "limit": 5},
            max_retries=2,
        )
        items = (data.get("artists") or {}).get("items") or []
        for artist in items:
            if artist.get("id") == spotify_id:
                return _normalize_genres(artist)
        name_key = artist_name.strip().lower()
        for artist in items:
            if (artist.get("name") or "").strip().lower() == name_key:
                return _normalize_genres(artist)
    except httpx.HTTPStatusError as err:
        code = err.response.status_code
        if code not in (403, 429):
            print(f"[ETL WARNING] search '{artist_name}': HTTP {code}")
    return []


def backfill_genres_from_top_artists(
    conn,
    token: str,
    raw_top: list[dict] | None = None,
) -> tuple[int, int]:
    """
    Rellena genres desde GET /me/top/artists (endpoint de usuario).

    Returns:
        tuple[int, int]: (filas actualizadas, artistas del top con genres en la API)
    """
    raw = raw_top if raw_top is not None else extract_top_artists(token)
    with_genres_in_api = sum(1 for item in raw if _normalize_genres(item))
    updated = 0
    with conn.cursor() as cur:
        for item in raw:
            sid = item.get("id")
            genres = _normalize_genres(item)
            if not sid or not genres:
                continue
            cur.execute(
                """
                UPDATE dwh.dim_artists
                SET genres = %s::text[], loaded_at = CURRENT_TIMESTAMP
                WHERE spotify_id = %s
                  AND (genres IS NULL OR cardinality(genres) = 0)
                """,
                (genres, sid),
            )
            updated += cur.rowcount
    if raw:
        print(
            f"[ETL INFO] Top artists: {with_genres_in_api}/{len(raw)} traen genres en API; "
            f"actualizados en DWH: {updated}"
        )
    return updated, with_genres_in_api


def backfill_genres_via_search(conn, token: str, limit: int = _SEARCH_GENRE_LIMIT) -> int:
    """Rellena genres vacios buscando por nombre (cuando el top no trae genres)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT spotify_id, name FROM dwh.dim_artists
            WHERE genres IS NULL OR cardinality(genres) = 0
            ORDER BY popularity DESC NULLS LAST, name
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()

    if not rows:
        return 0

    updated = 0
    with conn.cursor() as cur:
        for sid, name in rows:
            time.sleep(_SEARCH_DELAY_SECONDS)
            genres = _fetch_genres_via_search(token, name, sid)
            if not genres:
                continue
            cur.execute(
                """
                UPDATE dwh.dim_artists
                SET genres = %s::text[], loaded_at = CURRENT_TIMESTAMP
                WHERE spotify_id = %s
                """,
                (genres, sid),
            )
            updated += cur.rowcount

    if updated:
        print(f"[ETL INFO] Genres via /search: {updated} artistas actualizados.")
    return updated


def sync_artist_genres(
    conn,
    token: str,
    raw_top: list[dict] | None = None,
    *,
    musicbrainz_limit: int = 30,
) -> dict:
    """
    Sincroniza genres: Spotify top -> search -> MusicBrainz.
    Spotify suele devolver genres:[] desde 2025; MusicBrainz es el fallback principal.
    """
    from_top, top_with_genres = backfill_genres_from_top_artists(conn, token, raw_top)
    from_search = backfill_genres_via_search(conn, token)
    from_musicbrainz = backfill_genres_via_musicbrainz(conn, limit=musicbrainz_limit)
    if top_with_genres == 0 and from_musicbrainz == 0 and from_search == 0:
        print(
            "[ETL INFO] Spotify no expone genres (API vacia). "
            "Se usaron tags de MusicBrainz cuando hubo coincidencia."
        )
    return {
        "genres_backfilled_from_top": from_top,
        "genres_backfilled_from_search": from_search,
        "genres_backfilled_from_musicbrainz": from_musicbrainz,
        "top_artists_with_genres_in_api": top_with_genres,
        "spotify_genres_available": top_with_genres > 0,
    }


def backfill_dim_artists_metadata(
    conn,
    token: str,
    limit: int = 50,
    *,
    use_catalog_api: bool = False,
) -> int:
    """Actualiza popularity/genres/followers NULL. Catalogo desactivado por defecto (403)."""
    if not use_catalog_api:
        return 0

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT spotify_id FROM dwh.dim_artists
            WHERE popularity IS NULL
               OR genres IS NULL
               OR genres = '{}'
               OR followers_count IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        spotify_ids = [row[0] for row in cur.fetchall()]

    if not spotify_ids:
        return 0

    metadata_by_id = _fetch_artists_by_ids(token, spotify_ids)
    updated = 0
    with conn.cursor() as cur:
        for sid, meta in metadata_by_id.items():
            cur.execute(
                """
                UPDATE dwh.dim_artists SET
                    popularity = COALESCE(%s, popularity),
                    followers_count = COALESCE(%s, followers_count),
                    genres = CASE
                        WHEN %s::text[] IS NOT NULL AND cardinality(%s::text[]) > 0
                        THEN %s::text[]
                        ELSE genres
                    END,
                    loaded_at = CURRENT_TIMESTAMP
                WHERE spotify_id = %s
                """,
                (
                    meta.get("popularity"),
                    _followers_total(meta),
                    meta.get("genres") or [],
                    meta.get("genres") or [],
                    meta.get("genres") or [],
                    sid,
                ),
            )
            updated += cur.rowcount
    return updated


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_top_artists(
    raw_artists: list[dict],
    *,
    use_rank_fallback: bool = False,
) -> list[dict]:
    """
    Normaliza la lista cruda de artistas de Spotify al modelo de dwh.dim_artists.

    Args:
        raw_artists (list[dict]): Lista cruda retornada por extract_top_artists.
        use_rank_fallback (bool): Si True y falta popularity, usa ranking 100, 98, 96...

    Returns:
        list[dict]: Lista de dicts listos para insertar en dim_artists.
    """
    result = []
    for index, item in enumerate(raw_artists):
        spotify_id = item.get("id")
        if not spotify_id:
            continue

        popularity = item.get("popularity")
        if popularity is None and use_rank_fallback:
            popularity = max(1, 100 - index * 2)

        genres = _normalize_genres(item)

        result.append({
            "spotify_id": spotify_id,
            "name": item.get("name") or "Unknown",
            "popularity": popularity,
            "followers_count": _followers_total(item),
            "genres": genres,
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
                    popularity = CASE
                        WHEN EXCLUDED.popularity IS NOT NULL
                        THEN EXCLUDED.popularity
                        ELSE dwh.dim_artists.popularity
                    END,
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
            ORDER BY popularity DESC NULLS LAST, followers_count DESC NULLS LAST, name
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    result = []
    for row in rows:
        item = dict(row)
        if item.get("genres") is None:
            item["genres"] = []
        result.append(item)
    return result
