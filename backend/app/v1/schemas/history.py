"""
filename: history.py (schemas)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Schemas Pydantic para el historial de reproducciones (fact_listening_history).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HistoryBase(BaseModel):
    track_spotify_id: str
    artist_spotify_id: str
    played_at: datetime
    hour_of_day: int | None = None
    day_of_week: str | None = None
    context_type: str | None = None


class HistoryRequest(HistoryBase):
    """Payload de entrada del historial (datos transformados de Spotify)."""
    pass


class HistoryResponse(HistoryBase):
    """Payload de salida del historial (incluye campos generados por la DB)."""
    id: int
    user_id: int
    track_id: int
    artist_id: int

    model_config = ConfigDict(from_attributes=True)
