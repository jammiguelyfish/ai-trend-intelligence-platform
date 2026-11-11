import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.models import document, embedding, source, summary, topic, trend  # noqa: F401
from backend.app.pipelines.etl import ingest_items
from backend.app.scraping.schemas import RawItem


def _item(title, ext_id="42"):
    return RawItem(source="hackernews", external_id=ext_id, title=title, content="")


async def _run():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as s:
        first = await ingest_items(s, [_item("Winner of the Booker prize")])
    async with Session() as s:
        # same story, retitled upstream: must not crash on the unique constraint
        second = await ingest_items(s, [_item("Winner of the Booker"), _item("Other", "43")])
    await engine.dispose()
    return len(first), len(second)


def test_ingest_skips_items_already_stored_under_a_new_title():
    assert asyncio.run(_run()) == (1, 1)
