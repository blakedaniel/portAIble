"""Async SQLAlchemy engine + session factory + lifecycle helpers."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .base import Base
from . import models  # noqa: F401  — register tables on Base.metadata

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str) -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine

    if database_url.startswith("sqlite+aiosqlite:///"):
        # Ensure the parent dir exists (otherwise aiosqlite fails opaquely).
        db_path = Path(database_url.replace("sqlite+aiosqlite:///", "", 1))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    _engine = create_async_engine(database_url, future=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    logger.info("DB engine initialized: %s", database_url)
    return _engine


async def create_all() -> None:
    """Create all tables — used for first-run bootstrap and tests.

    Production should run Alembic migrations instead; this is the lightweight path
    we use in lifespan startup until we add the first Alembic revision.
    """
    if _engine is None:
        raise RuntimeError("init_engine() must be called before create_all()")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession with commit-on-success / rollback-on-error semantics."""
    if _sessionmaker is None:
        raise RuntimeError("init_engine() must be called before session_scope()")
    async with _sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("init_engine() must be called before get_sessionmaker()")
    return _sessionmaker


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
