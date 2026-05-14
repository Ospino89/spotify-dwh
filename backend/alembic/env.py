"""
filename: env.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Configuracion de Alembic para leer DATABASE_URL desde pydantic Settings.
             Soporta migraciones en modo offline (solo SQL) y online (contra Neon).
"""

import sys
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Agregar backend/ al path para poder importar app.*
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

# ---------------------------------------------------------------------------
# Config de Alembic (lee alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# Inyectar DATABASE_URL desde pydantic Settings — sobreescribe el valor vacio de alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para autogenerate (None por ahora — usamos DDL manual en las migraciones)
target_metadata = None


# ---------------------------------------------------------------------------
# Modo offline — genera SQL sin conectarse a la DB
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Corre las migraciones en modo offline.
    Genera un script SQL sin necesitar conexion activa a la base de datos.

    Args:
        None

    Returns:
        None
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Modo online — corre las migraciones contra Neon directamente
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """
    Corre las migraciones en modo online conectandose a PostgreSQL en Neon.
    Este es el modo que se usa con: alembic upgrade head

    Args:
        None

    Returns:
        None
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()