"""Summary generation service (Ollama-backed)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.ollama import summarize
from backend.app.config import settings
from backend.app.models import Document, Summary


async def summarize_document(session: AsyncSession, document_id: int) -> Summary | None:
    doc = (
        await session.execute(select(Document).where(Document.id == document_id))
    ).scalar_one_or_none()
    if not doc:
        return None

    text = f"Title: {doc.title}\n\n{doc.content or ''}".strip()
    content = await summarize(text)
    s = Summary(
        document_id=doc.id,
        model=settings.ollama_model,
        content=content,
    )
    session.add(s)
    await session.commit()
    return s
