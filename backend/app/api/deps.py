"""Common FastAPI dependencies."""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import SessionLocal


async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
