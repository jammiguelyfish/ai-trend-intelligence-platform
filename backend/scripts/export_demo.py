"""Export a static snapshot of the API for the GitHub Pages demo.

The hosted demo has no backend, so this writes the data the frontend would
have fetched as JSON files into ``frontend/public/demo/``. Semantic search
needs the embedding model, so it is precomputed for a set of example queries;
free-text search in the demo falls back to keyword matching in the browser.

Usage:
    python -m backend.scripts.export_demo
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import func, select

from backend.app.api.topics import list_topics
from backend.app.db.session import SessionLocal
from backend.app.models import Document, Source
from backend.app.services.search import semantic_search
from backend.app.services.trends import list_buckets, list_trends

OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "demo"

EXAMPLE_QUERIES = [
    "running language models locally on a laptop",
    "AI agents that use tools",
    "reducing hallucinations",
    "fine-tuning small models",
    "making inference faster on GPUs",
    "AI coding assistants",
    "retrieval augmented generation",
    "open source versus closed models",
]


def write(name: str, data) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


async def main() -> None:
    async with SessionLocal() as session:
        sources = (await session.execute(select(Source))).scalars().all()
        write("sources.json", [
            {"id": s.id, "name": s.name, "kind": s.kind, "enabled": s.enabled} for s in sources
        ])

        docs = (await session.execute(select(Document).order_by(Document.id))).scalars().all()
        write("documents.json", [
            {
                "id": d.id,
                "title": d.title,
                "url": d.url,
                "snippet": (d.content or "")[:300],
                "published_at": d.published_at.isoformat() if d.published_at else None,
            }
            for d in docs
        ])

        buckets = await list_buckets(session, limit=14)
        write("buckets.json", {"buckets": buckets})
        for b in buckets:
            write(f"trends/{b}.json", {"bucket": b, "items": await list_trends(session, bucket=b, limit=50)})
        write("trends/latest.json", {"bucket": None, "items": await list_trends(session, limit=50)})

        write("topics.json", await list_topics(session))

        examples = {}
        for q in EXAMPLE_QUERIES:
            examples[q] = await semantic_search(session, q, k=10)
        write("search_examples.json", {"queries": EXAMPLE_QUERIES, "results": examples})

        vectors = (await session.execute(select(func.count(Document.id)))).scalar_one()
        write("health.json", {"status": "demo", "vectors": vectors})

    print(f"wrote demo snapshot to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
