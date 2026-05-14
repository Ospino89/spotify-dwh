"""
filename: config.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Configuracion central de la aplicacion usando pydantic-settings.
             Carga todas las variables de entorno desde el archivo .env.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sube desde app/core/config.py -> app/core -> app -> backend -> raiz del proyecto
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """
    Clase de configuracion. Cada atributo mapea a una variable de entorno.
    Carga el .env desde la raiz del proyecto sin importar desde donde se corra uvicorn.
    """

    # Spotify OAuth
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://127.0.0.1:8000/v1/auth/callback"
    

    # Base de datos
    database_url: str

    # App
    app_name: str = "Spotify DWH API"
    app_version: str = "1.0.0"
    secret_key: str
    frontend_url: str = "http://localhost:3000"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")


# Instancia global — importar desde cualquier modulo con: from app.core.config import settings
settings = Settings()