"""Async SQLAlchemy engine and session factory."""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables if they don't exist (used for SQLite/local dev)."""
    from backend.app.db.base import Base
    from backend.app.models import (  # noqa: F401  (ensure models imported)
        document,
        embedding,
        source,
        summary,
        topic,
        trend,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
