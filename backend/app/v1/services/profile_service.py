"""
filename: profile_service.py
author: Equipo Spotify DWH
date: 2025-05-10
version: 1.0
description: Servicio para obtener el perfil del usuario autenticado desde dim_users.
"""

import psycopg2.extras


def get_user_profile(conn, spotify_id: str) -> dict | None:
    """
    Recupera el perfil del usuario desde dwh.dim_users.

    Args:
        conn: Conexion activa a PostgreSQL.
        spotify_id (str): ID del usuario en Spotify (extraido del JWT).

    Returns:
        dict | None: Fila de dim_users como dict, o None si el usuario no existe.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT user_id, spotify_id, display_name, email, country,
                   followers, product, loaded_at
            FROM dwh.dim_users
            WHERE spotify_id = %s
            """,
            (spotify_id,),
        )
        row = cur.fetchone()
    return dict(row) if row else None
