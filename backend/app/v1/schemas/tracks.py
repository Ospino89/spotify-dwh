"""
filename: tracks.py (schemas)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Schemas Pydantic para tracks (dim_tracks).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrackBase(BaseModel):
    spotify_id: str
    name: str
    artist_spotify_id: str | None = None
    album_name: str | None = None
    duration_ms: int | None = None
    popularity: int | None = None
    explicit: bool = False


class TrackRequest(TrackBase):
    """Payload de entrada del track (datos transformados de Spotify)."""
    pass


class TrackResponse(TrackBase):
    """Payload de salida del track (incluye campos generados por la DB)."""
    track_id: int
    artist_id: int | None = None
    loaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
