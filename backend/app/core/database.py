"""
filename: database.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Gestion de la conexion a PostgreSQL (Neon) usando psycopg2.
             Provee un context manager para obtener y liberar conexiones de forma segura.
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from app.core.config import settings


def get_connection():
    """
    Crea y retorna una conexion directa a PostgreSQL usando DATABASE_URL del .env.

    Returns:
        psycopg2.connection: Conexion activa a la base de datos.

    Raises:
        psycopg2.OperationalError: Si no puede conectarse a la base de datos.
    """
    return psycopg2.connect(str(settings.database_url))

@contextmanager
def get_db():
    """
    Context manager para obtener una conexion con commit/rollback automatico.

    Yields:
        psycopg2.connection: Conexion activa. Hace commit al salir sin errores,
                             rollback si hay una excepcion.

    Example:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_dependency():
    """
    Dependency de FastAPI para inyectar una conexion en los endpoints.
    Usar con Depends(get_db_dependency).

    Yields:
        psycopg2.connection: Conexion activa a la base de datos.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
