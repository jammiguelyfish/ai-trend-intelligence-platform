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
