"""End-to-end pipeline runner: scrape -> ETL -> embed -> trends -> topics.

Usage:
    python -m backend.scripts.run_pipeline
"""
from __future__ import annotations

import asyncio
from itertools import chain

from backend.app.db.session import SessionLocal, init_db
from backend.app.pipelines.embed import embed_pending
from backend.app.pipelines.etl import ingest_items
from backend.app.pipelines.topics import cluster_topics
from backend.app.pipelines.trends import compute_daily_trends
from backend.app.scraping.arxiv import scrape_arxiv
from backend.app.scraping.github import scrape_github_trending
from backend.app.scraping.hackernews import scrape_hackernews
from backend.app.scraping.reddit import scrape_reddit
from backend.app.utils.logging import configure_logging, get_logger


async def main() -> None:
    configure_logging()
    log = get_logger("pipeline")
    await init_db()

    log.info("pipeline.scrape")
    batches = await asyncio.gather(
        scrape_reddit(),
        scrape_hackernews(limit=150),
        scrape_github_trending(),
        scrape_arxiv(max_results=200),
        return_exceptions=True,
    )
    items = list(
        chain.from_iterable(b for b in batches if isinstance(b, list))
    )
    log.info("pipeline.scraped", total=len(items))

    async with SessionLocal() as session:
        await ingest_items(session, items)
    async with SessionLocal() as session:
        await embed_pending(session)
    async with SessionLocal() as session:
        await compute_daily_trends(session)
    async with SessionLocal() as session:
        await cluster_topics(session)

    log.info("pipeline.done")


if __name__ == "__main__":
    asyncio.run(main())
