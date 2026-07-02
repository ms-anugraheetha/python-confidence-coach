"""
app/db/session.py — Async SQLAlchemy engine, session factory, and FastAPI dependency.

WHY THIS FILE EXISTS:
  Three things live here that are tightly coupled:
    1. The engine — the connection pool to PostgreSQL.
    2. The session factory — creates sessions from the engine.
    3. get_db() — the FastAPI dependency that routes use to get a session.

  Keeping them together means there's one place to change connection settings,
  one place to change session behavior, and one place to change the DI pattern.

USAGE IN ROUTE HANDLERS:
  from fastapi import Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.db.session import get_db

  @router.post("/chat/message")
  async def send_message(
      db: AsyncSession = Depends(get_db),
      ...
  ):
      # db is a live session, committed on success, rolled back on exception
      user = await user_repo.get_by_id(db, user_id)

USAGE IN LIFESPAN (main.py):
  from app.db.session import init_db, close_db
  await init_db()   # startup
  await close_db()  # shutdown
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# Module-level engine — one per application process.
# This is the connection pool. It is created once and reused for the lifetime
# of the process. Never create a new engine per request.
#
# pool_size:    Persistent connections kept open (ready to use immediately).
# max_overflow: Extra connections allowed under load. These are created on demand
#               and closed when the burst subsides.
# echo:         Log every SQL statement in development. Off in production.
# pool_pre_ping: Test connections before use. Recovers from DB restarts silently.

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.is_development,
    pool_pre_ping=True,
    # pool_recycle prevents "server closed the connection unexpectedly" errors
    # on long-running servers by recycling connections every 30 minutes.
    pool_recycle=1800,
)

# ── Session factory ───────────────────────────────────────────────────────────
# async_sessionmaker creates AsyncSession instances on demand.
#
# expire_on_commit=False:
#   By default, SQLAlchemy expires ORM objects after commit, forcing a new
#   SELECT to access any attribute. In async FastAPI handlers, the session is
#   already closed by then — causing MissingGreenlet errors.
#   expire_on_commit=False keeps values in memory, which is what we want
#   for API handlers that read a value and immediately return it.
#
# class_=AsyncSession:
#   Explicit. Makes mypy happy and documents intent clearly.

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,    # Flushes pending changes before queries (correct default)
    autocommit=False,  # Explicit transaction management via get_db()
)


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.

    Transaction behaviour:
      - The session is yielded inside a context manager.
      - On SUCCESS (no exception): await session.commit() is called automatically.
      - On EXCEPTION: await session.rollback() is called, then the exception re-raises.

    This means route handlers NEVER need to call commit() or rollback() manually.
    They just use the session — the dependency handles the transaction boundary.

    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            db: AsyncSession = Depends(get_db),
        ):
            user = await user_repo.get_by_id(db, user_id)
            if not user:
                raise NotFoundError("User", user_id)
            return user
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Lifespan helpers ──────────────────────────────────────────────────────────
# Called from main.py's lifespan context manager.

async def init_db() -> None:
    """
    Verify the database is reachable at startup.

    Does NOT create tables — that's Alembic's job.
    Just confirms the connection pool can open a connection.
    Fails fast at startup rather than on the first request.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info(
            "database_connected",
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        raise


async def close_db() -> None:
    """
    Dispose the connection pool on shutdown.

    This closes all idle connections cleanly, preventing "connection still
    open" warnings in PostgreSQL logs.
    """
    await engine.dispose()
    logger.info("database_pool_closed")
