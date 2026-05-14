"""
filename: api.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Router principal de la version 1 de la API.
             Registra todos los sub-routers con sus prefijos y tags.
             Este archivo es el unico lugar donde se conectan los routers a la app.
"""

from fastapi import APIRouter

from app.v1.routers import auth, profile, artists, tracks, history, etl

router = APIRouter()

router.include_router(auth.router,    prefix="/auth",    tags=["auth"])
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(artists.router, prefix="/artists", tags=["artists"])
router.include_router(tracks.router,  prefix="/tracks",  tags=["tracks"])
router.include_router(history.router, prefix="/history", tags=["history"])
router.include_router(etl.router,     prefix="/etl",     tags=["etl"])