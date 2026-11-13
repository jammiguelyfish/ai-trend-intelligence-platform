import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.models import Trend, document, embedding, source, summary, topic, trend  # noqa: F401
from backend.app.services.trends import list_trends


async def _run():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        s.add_all(
            [
                Trend(bucket="2026-11-09", term="models", count=50, delta=50.0),
                Trend(bucket="2026-11-10", term="models", count=40, delta=-10.0),
                Trend(bucket="2026-11-10", term="agents", count=30, delta=30.0),
            ]
        )
        await s.commit()
        latest = await list_trends(s)
        explicit = await list_trends(s, bucket="2026-11-09")
    await engine.dispose()
    return latest, explicit


def test_default_is_latest_day_and_explicit_bucket_still_works():
    latest, explicit = asyncio.run(_run())
    assert {r["bucket"] for r in latest} == {"2026-11-10"}
    assert [r["term"] for r in latest] == ["agents", "models"]
    assert [r["term"] for r in explicit] == ["models"]


async def _phrase_run():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        s.add_all(
            [
                Trend(bucket="2026-11-10", term="model", count=60, delta=40.0),
                Trend(bucket="2026-11-10", term="foundation model", count=25, delta=24.0),
            ]
        )
        await s.commit()
        rows = await list_trends(s)
    await engine.dispose()
    return rows


def test_phrases_outrank_generic_words_with_a_similar_rise():
    assert [r["term"] for r in asyncio.run(_phrase_run())][0] == "foundation model"


async def _df_run():
    from datetime import datetime, timezone

    from sqlalchemy import select

    from backend.app.pipelines.etl import ingest_items
    from backend.app.pipelines.trends import compute_daily_trends
    from backend.app.scraping.schemas import RawItem

    now = datetime.now(timezone.utc)

    def item(i, text):
        return RawItem(source="hackernews", external_id=str(i), title=text, content="", published_at=now)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        await ingest_items(
            s,
            [
                item(1, "prefill " * 20 + "decode"),
                item(2, "agents everywhere"),
                item(3, "building agents"),
            ],
        )
    async with Session() as s:
        await compute_daily_trends(s)
        rows = {r.term: r.count for r in (await s.execute(select(Trend))).scalars().all()}
    await engine.dispose()
    return rows


def test_terms_are_counted_once_per_document_and_need_two_documents():
    rows = asyncio.run(_df_run())
    assert rows.get("agent") == 2
    assert "prefill" not in rows  # 20 mentions, but in a single document
