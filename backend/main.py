"""
filename: main.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Punto de entrada de la aplicacion FastAPI.
             Configura CORS, registra todos los routers bajo el prefijo /v1
             y expone los endpoints de health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.v1.api import router as v1_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — FRONTEND_URL + origenes locales de Vite en desarrollo
# ---------------------------------------------------------------------------
_frontend = str(settings.frontend_url).rstrip("/")
_cors_origins = list({
    _frontend,
    f"{_frontend}/",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
})
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — todos bajo /v1
# ---------------------------------------------------------------------------
app.include_router(v1_router, prefix="/v1")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["health"])
def root():
    """
    Endpoint raiz. Verifica que la API esta corriendo.

    Returns:
        dict: Nombre y version de la app.
    """
    return {"app": settings.app_name, "version": settings.app_version, "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    """
    Health check para monitoreo o despliegue.

    Returns:
        dict: Status 'healthy'.
    """
    return {"status": "healthy"}



