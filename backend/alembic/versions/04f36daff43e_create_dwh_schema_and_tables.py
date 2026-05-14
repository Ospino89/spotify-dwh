"""create dwh schema and tables

Revision ID: 0001
Revises: 
Create Date: 2025-05-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------------------
    # Schema DWH
    # ---------------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS dwh")

    # ---------------------------------------------------------------------------
    # public.pkce_sessions — estado temporal del flujo OAuth PKCE
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.pkce_sessions (
            state      TEXT PRIMARY KEY,
            verifier   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------------------------------------------------
    # dwh.dim_users — dimension de usuarios
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS dwh.dim_users (
            user_id               SERIAL PRIMARY KEY,
            spotify_id            TEXT UNIQUE NOT NULL,
            display_name          TEXT,
            email                 TEXT,
            country               TEXT,
            followers             INTEGER,
            product               TEXT,
            spotify_access_token  TEXT,
            spotify_refresh_token TEXT,
            token_expires_at      TIMESTAMP WITH TIME ZONE,
            loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------------------------------------------------
    # dwh.dim_artists — dimension de artistas
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS dwh.dim_artists (
            artist_id       SERIAL PRIMARY KEY,
            spotify_id      TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            popularity      INTEGER,
            followers_count INTEGER,
            genres          TEXT[],
            loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------------------------------------------------
    # dwh.dim_tracks — dimension de canciones
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS dwh.dim_tracks (
            track_id    SERIAL PRIMARY KEY,
            spotify_id  TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            artist_id   INTEGER REFERENCES dwh.dim_artists(artist_id),
            album_name  TEXT,
            duration_ms INTEGER,
            popularity  INTEGER,
            explicit    BOOLEAN DEFAULT FALSE,
            loaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------------------------------------------------
    # dwh.fact_listening_history — tabla de hechos (grain: user + played_at)
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS dwh.fact_listening_history (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES dwh.dim_users(user_id),
            track_id    INTEGER NOT NULL REFERENCES dwh.dim_tracks(track_id),
            artist_id   INTEGER NOT NULL REFERENCES dwh.dim_artists(artist_id),
            played_at   TIMESTAMP WITH TIME ZONE NOT NULL,
            hour_of_day INTEGER,
            day_of_week TEXT,
            context_type TEXT,
            UNIQUE (user_id, played_at)
        )
    """)

    # ---------------------------------------------------------------------------
    # dwh.etl_audit — registro de cada ejecucion del pipeline ETL
    # ---------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS dwh.etl_audit (
            audit_id         SERIAL PRIMARY KEY,
            spotify_user_id  TEXT NOT NULL,
            status           TEXT NOT NULL,
            started_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            finished_at      TIMESTAMP WITH TIME ZONE,
            duration_ms      INTEGER,
            artists_inserted INTEGER DEFAULT 0,
            artists_skipped  INTEGER DEFAULT 0,
            tracks_inserted  INTEGER DEFAULT 0,
            tracks_skipped   INTEGER DEFAULT 0,
            history_inserted INTEGER DEFAULT 0,
            history_skipped  INTEGER DEFAULT 0,
            cursor_after_ms  BIGINT,
            cursor_next_ms   BIGINT,
            error_msg        TEXT
        )
    """)


def downgrade() -> None:
    # Eliminar en orden inverso para respetar las FK
    op.execute("DROP TABLE IF EXISTS dwh.etl_audit")
    op.execute("DROP TABLE IF EXISTS dwh.fact_listening_history")
    op.execute("DROP TABLE IF EXISTS dwh.dim_tracks")
    op.execute("DROP TABLE IF EXISTS dwh.dim_artists")
    op.execute("DROP TABLE IF EXISTS dwh.dim_users")
    op.execute("DROP TABLE IF EXISTS public.pkce_sessions")
    op.execute("DROP SCHEMA IF EXISTS dwh")