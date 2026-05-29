"""Topic clustering using HDBSCAN over recent document embeddings."""
from __future__ import annotations

from collections import Counter
from typing import List

import numpy as np
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.embeddings import store
from backend.app.embeddings.model import embed_texts
from backend.app.models import Document, DocumentTopic, Topic
from backend.app.pipelines.trends import _tokens
from backend.app.utils.logging import get_logger

log = get_logger(__name__)


async def cluster_topics(
    session: AsyncSession, max_docs: int = 1000, min_cluster_size: int = 5
) -> List[Topic]:
    docs = list(
        (
            await session.execute(
                select(Document).order_by(Document.id.desc()).limit(max_docs)
            )
        )
        .scalars()
        .all()
    )
    if len(docs) < min_cluster_size:
        log.info("topics.too_few", n=len(docs))
        return []

    texts = [f"{d.title}\n{d.content or ''}" for d in docs]
    X = embed_texts(texts)

    import hdbscan

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size, metric="euclidean"
    )
    labels = clusterer.fit_predict(X.astype(np.float64))

    # reset topic data
    await session.execute(delete(DocumentTopic))
    await session.execute(delete(Topic))

    out: List[Topic] = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        members = [d for d, l in zip(docs, labels) if l == cid]
        kw_counter: Counter = Counter()
        for m in members:
            kw_counter.update(_tokens(f"{m.title} {m.content or ''}"))
        keywords = [w for w, _ in kw_counter.most_common(8)]
        label = ", ".join(keywords[:3]) or f"topic-{cid}"
        topic = Topic(
            label=label[:256],
            keywords=", ".join(keywords)[:1024],
            size=len(members),
        )
        session.add(topic)
        await session.flush()
        for m in members:
            session.add(DocumentTopic(document_id=m.id, topic_id=topic.id, score=1.0))
        out.append(topic)

    await session.commit()
    log.info("topics.done", clusters=len(out))
    _ = store  # ensure import preserved for side-effect free linter
    return out
