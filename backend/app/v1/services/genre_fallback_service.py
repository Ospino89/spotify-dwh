"""
Fallback de generos cuando Spotify devuelve genres: [] (cambio API ~2025).
Usa MusicBrainz (sin API key, 1 req/seg).
"""

import time
import httpx

_MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"
_USER_AGENT = "mi-spotify-wrapped/1.0 (educational-dwh-project)"
_MIN_INTERVAL_SEC = 1.1
_MAX_TAGS = 5
_last_request_at = 0.0


def _throttle() -> None:
    global _last_request_at
    elapsed = time.time() - _last_request_at
    if elapsed < _MIN_INTERVAL_SEC:
        time.sleep(_MIN_INTERVAL_SEC - elapsed)
    _last_request_at = time.time()


def fetch_genres_musicbrainz(artist_name: str) -> list[str]:
    """
    Busca tags/generos de un artista en MusicBrainz por nombre.

    Args:
        artist_name (str): Nombre del artista en dim_artists.

    Returns:
        list[str]: Hasta 5 tags ordenados por relevancia, o lista vacia.
    """
    name = (artist_name or "").strip()
    if not name:
        return []

    headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}

    try:
        _throttle()
        with httpx.Client(timeout=20.0) as client:
            search = client.get(
                f"{_MUSICBRAINZ_BASE}/artist",
                params={"query": f'artist:"{name}"', "fmt": "json", "limit": 1},
                headers=headers,
            )
            if search.status_code != 200:
                return []
            artists = search.json().get("artists") or []
            if not artists:
                return []
            mbid = artists[0].get("id")
            if not mbid:
                return []

            _throttle()
            detail = client.get(
                f"{_MUSICBRAINZ_BASE}/artist/{mbid}",
                params={"inc": "tags+genres", "fmt": "json"},
                headers=headers,
            )
            if detail.status_code != 200:
                return []
            body = detail.json()

            genre_names = [
                g.get("name")
                for g in (body.get("genres") or [])
                if g and g.get("name")
            ]
            if genre_names:
                return genre_names[:_MAX_TAGS]

            tags = body.get("tags") or []
            ranked = sorted(tags, key=lambda t: t.get("count", 0), reverse=True)
            return [
                t["name"]
                for t in ranked[:_MAX_TAGS]
                if t.get("name")
            ]
    except (httpx.HTTPError, KeyError, TypeError) as err:
        print(f"[ETL WARNING] MusicBrainz '{name}': {err}")
        return []


def backfill_genres_via_musicbrainz(conn, limit: int = 30) -> int:
    """Actualiza dim_artists.genres usando MusicBrainz para filas vacias."""
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
        for _sid, name in rows:
            genres = fetch_genres_musicbrainz(name)
            if not genres:
                continue
            cur.execute(
                """
                UPDATE dwh.dim_artists
                SET genres = %s::text[], loaded_at = CURRENT_TIMESTAMP
                WHERE spotify_id = %s
                """,
                (genres, _sid),
            )
            updated += cur.rowcount

    if updated:
        print(f"[ETL INFO] Genres via MusicBrainz: {updated} artistas actualizados.")
    else:
        print(
            "[ETL INFO] MusicBrainz no devolvio tags para este lote "
            f"({len(rows)} artistas probados)."
        )
    return updated
