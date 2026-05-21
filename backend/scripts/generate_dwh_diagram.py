"""Genera backend/docs/dwh-diagram.excalidraw con el star schema del DWH."""

import json
import random
import time
from pathlib import Path


def gen_id() -> str:
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16))


def rect(x: float, y: float, w: float, h: float, bg: str, text: str) -> tuple[dict, dict, str]:
    rid = gen_id()
    tid = gen_id()
    seed = random.randint(1, 2**31)
    nonce = random.randint(1, 2**31)
    ts = int(time.time() * 1000)
    rectangle = {
        "id": rid,
        "type": "rectangle",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": bg,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3},
        "seed": seed,
        "version": 1,
        "versionNonce": nonce,
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": tid}],
        "updated": ts,
        "link": None,
        "locked": False,
    }
    label = {
        "id": tid,
        "type": "text",
        "x": x + 10,
        "y": y + 10,
        "width": w - 20,
        "height": h - 20,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": seed + 1,
        "version": 1,
        "versionNonce": nonce + 1,
        "isDeleted": False,
        "boundElements": [],
        "updated": ts,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": 14,
        "fontFamily": 1,
        "textAlign": "left",
        "verticalAlign": "top",
        "containerId": rid,
        "originalText": text,
        "autoResize": True,
        "lineHeight": 1.25,
    }
    return rectangle, label, rid


def arrow(start_id: str, end_id: str, sx: float, sy: float, ex: float, ey: float) -> dict:
    ts = int(time.time() * 1000)
    return {
        "id": gen_id(),
        "type": "arrow",
        "x": sx,
        "y": sy,
        "width": ex - sx,
        "height": ey - sy,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 2},
        "seed": random.randint(1, 2**31),
        "version": 1,
        "versionNonce": random.randint(1, 2**31),
        "isDeleted": False,
        "boundElements": [],
        "updated": ts,
        "link": None,
        "locked": False,
        "points": [[0, 0], [ex - sx, ey - sy]],
        "lastCommittedPoint": None,
        "startBinding": {"elementId": start_id, "focus": 0, "gap": 5},
        "endBinding": {"elementId": end_id, "focus": 0, "gap": 5},
        "startArrowhead": None,
        "endArrowhead": "arrow",
    }


def title_text() -> dict:
    ts = int(time.time() * 1000)
    text = "Star Schema — Mi Spotify Wrapped DWH"
    return {
        "id": gen_id(),
        "type": "text",
        "x": 220,
        "y": 0,
        "width": 620,
        "height": 36,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 1,
        "version": 1,
        "versionNonce": 2,
        "isDeleted": False,
        "boundElements": [],
        "updated": ts,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": 24,
        "fontFamily": 1,
        "textAlign": "center",
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "autoResize": True,
        "lineHeight": 1.25,
    }


def legend_text() -> dict:
    ts = int(time.time() * 1000)
    text = "Azul = dimension usuario | Verde = dimensiones contenido | Amarillo = hechos | Rojo = auditoria ETL"
    return {
        "id": gen_id(),
        "type": "text",
        "x": 120,
        "y": 820,
        "width": 820,
        "height": 24,
        "angle": 0,
        "strokeColor": "#495057",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": 3,
        "version": 1,
        "versionNonce": 4,
        "isDeleted": False,
        "boundElements": [],
        "updated": ts,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": 16,
        "fontFamily": 1,
        "textAlign": "center",
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "autoResize": True,
        "lineHeight": 1.25,
    }


def main() -> None:
    elements: list[dict] = []
    table_ids: dict[str, str] = {}

    def add_table(key: str, x: float, y: float, w: float, h: float, bg: str, text: str) -> None:
        rectangle, label, element_id = rect(x, y, w, h, bg, text)
        elements.extend([rectangle, label])
        table_ids[key] = element_id

    add_table(
        "users",
        400,
        50,
        280,
        210,
        "#a5d8ff",
        "dwh.dim_users\n─────────────\nPK  user_id\nUK  spotify_id\n    display_name, email\n    country, followers, product\n    spotify_access_token\n    spotify_refresh_token\n    token_expires_at\n    loaded_at",
    )
    add_table(
        "artists",
        40,
        340,
        280,
        190,
        "#b2f2bb",
        "dwh.dim_artists\n─────────────\nPK  artist_id\nUK  spotify_id\n    name, popularity\n    followers_count\n    genres TEXT[]\n    loaded_at",
    )
    add_table(
        "tracks",
        780,
        340,
        280,
        190,
        "#b2f2bb",
        "dwh.dim_tracks\n─────────────\nPK  track_id\nUK  spotify_id\nFK  artist_id → dim_artists\n    name, album_name\n    duration_ms, popularity\n    explicit, loaded_at",
    )
    add_table(
        "fact",
        360,
        580,
        360,
        230,
        "#ffec99",
        "dwh.fact_listening_history\n─────────────\nPK  id\nFK  user_id → dim_users\nFK  track_id → dim_tracks\nFK  artist_id → dim_artists\n    played_at\n    hour_of_day, day_of_week\n    context_type\nUK (user_id, played_at)",
    )
    add_table(
        "audit",
        780,
        620,
        280,
        170,
        "#ffc9c9",
        "dwh.etl_audit\n─────────────\nPK  audit_id\n    spotify_user_id\n    status, started_at, finished_at\n    duration_ms\n    artists/tracks/history inserted/skipped\n    cursor_after_ms, cursor_next_ms",
    )
    add_table(
        "pkce",
        40,
        50,
        240,
        110,
        "#e9ecef",
        "public.pkce_sessions\n─────────────\nPK  state\n    verifier\n(sesion OAuth temporal)",
    )

    elements.append(title_text())
    elements.append(legend_text())

    # FK: dimensiones → tabla de hechos
    elements.append(arrow(table_ids["users"], table_ids["fact"], 540, 260, 500, 580))
    elements.append(arrow(table_ids["artists"], table_ids["fact"], 320, 440, 400, 620))
    elements.append(arrow(table_ids["tracks"], table_ids["fact"], 780, 440, 680, 620))
    # FK: dim_tracks → dim_artists
    elements.append(arrow(table_ids["artists"], table_ids["tracks"], 320, 430, 780, 430))

    output = Path(__file__).resolve().parents[1] / "docs" / "dwh-diagram.excalidraw"
    output.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": 20,
            "viewBackgroundColor": "#f8f9fa",
        },
        "files": {},
    }
    output.write_text(json.dumps(document, indent=2), encoding="utf-8")
    print(f"Diagrama guardado en: {output}")


if __name__ == "__main__":
    main()
