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
from pydantic import AnyHttpUrl, SecretStr, PostgresDsn

# Sube desde app/core/config.py -> app/core -> app -> backend -> raiz del proyecto
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """
    Clase de configuracion. Cada atributo mapea a una variable de entorno.
    Carga el .env desde la raiz del proyecto sin importar desde donde se corra uvicorn.
    """

    # Spotify OAuth
    spotify_client_id: SecretStr
    spotify_client_secret: SecretStr
    spotify_redirect_uri: AnyHttpUrl
    

    # Base de datos
    database_url: PostgresDsn

    # App
    app_name: str 
    app_version: str
    secret_key: SecretStr
    frontend_url: AnyHttpUrl

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")


# Instancia global — importar desde cualquier modulo con: from app.core.config import settings
settings = Settings()