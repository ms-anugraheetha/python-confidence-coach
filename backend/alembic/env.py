"""
alembic/env.py — Alembic migration environment.

WHY THIS FILE EXISTS:
  Alembic runs this file for every migration command (upgrade, downgrade,
  revision --autogenerate). It has two modes:
    - offline: generates SQL scripts without a live DB connection
    - online:  connects to the DB and runs migrations directly

  ASYNC NOTE:
    Our engine is async (asyncpg). Alembic's default run_migrations_online()
    uses synchronous connections. We bridge this with asyncio.run() so
    Alembic (which is sync) can drive our async engine correctly.

HOW AUTOGENERATE WORKS:
  Alembic compares:
    1. The models registered in target_metadata (from our SQLAlchemy Base)
    2. The tables currently in the database
  And generates a migration file with the diff.

  For autogenerate to see all tables, every model module must be imported
  BEFORE target_metadata is read. We do this by importing from
  app.db.models (which imports all 5 models in its __init__.py).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# ── App imports ───────────────────────────────────────────────────────────────
# Import Settings FIRST so the DATABASE_URL is available.
from app.core.config import get_settings

# Import Base and all models so Alembic's autogenerate can see every table.
# This is the one place where importing * is intentional.
from app.db.base import Base
import app.db.models  # noqa: F401 — side effect: registers all models with Base.metadata

# ── Alembic config ────────────────────────────────────────────────────────────
config = context.config
settings = get_settings()

# Override the sqlalchemy.url from alembic.ini with our env-var-driven URL.
# This keeps DB credentials out of the committed config file.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure logging from alembic.ini (only if the ini has a logging section)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object Alembic uses for autogenerate comparison.
target_metadata = Base.metadata


# ── Offline mode ──────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Generate SQL scripts without a live DB connection.

    Usage: alembic upgrade head --sql > migration.sql

    Useful for:
      - Previewing what Alembic will do before running
      - Generating scripts for DBAs to review in production
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare server defaults so columns with server_default=func.now()
        # are detected correctly during autogenerate.
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────────────────────
def do_run_migrations(connection) -> None:
    """Called with a live synchronous connection inside asyncio.run()."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_server_default=True,
        # Include schemas if you ever add PostgreSQL schemas beyond 'public'
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations through it.

    We use NullPool here (not a connection pool) because Alembic runs
    migrations as a one-shot CLI command — pooling adds overhead with
    no benefit for a single-connection operation.
    """
    engine = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations (the normal mode)."""
    asyncio.run(run_async_migrations())


# ── Dispatch ──────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
