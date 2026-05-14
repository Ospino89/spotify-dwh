"""
filename: profile.py (schemas)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Schemas Pydantic para el perfil del usuario (dim_users).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    spotify_id: str
    display_name: str | None = None
    email: str | None = None
    country: str | None = None
    followers: int | None = None
    product: str | None = None


class ProfileRequest(ProfileBase):
    """Payload de entrada del perfil (datos crudos de Spotify)."""
    pass


class ProfileResponse(ProfileBase):
    """Payload de salida del perfil (incluye campos generados por la DB)."""
    user_id: int
    loaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
