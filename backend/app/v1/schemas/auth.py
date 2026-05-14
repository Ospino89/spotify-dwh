"""
filename: auth.py (schemas)
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Schemas Pydantic para el flujo de autenticacion OAuth PKCE con Spotify.
"""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Payload de respuesta al emitir el JWT propio de la app."""
    access_token: str
    token_type: str = "bearer"
    spotify_id: str


class PKCESessionBase(BaseModel):
    state: str
    verifier: str


class PKCESessionRequest(PKCESessionBase):
    """Payload de entrada para guardar una sesion PKCE."""
    pass


class PKCESessionResponse(PKCESessionBase):
    """Payload de salida de una sesion PKCE."""
    pass
