"""
filename: artists.py (schemas)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Schemas Pydantic para artistas (dim_artists).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ArtistBase(BaseModel):
    spotify_id: str
    name: str
    popularity: int | None = None
    followers_count: int | None = None
    genres: list[str] = []


class ArtistRequest(ArtistBase):
    """Payload de entrada del artista (datos crudos transformados de Spotify)."""
    pass


class ArtistResponse(ArtistBase):
    """Payload de salida del artista (incluye campos generados por la DB)."""
    artist_id: int
    loaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
