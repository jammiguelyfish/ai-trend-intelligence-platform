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


def cluster_embeddings(X: np.ndarray, min_cluster_size: int = 5) -> np.ndarray:
    """Cluster unit-norm embeddings with HDBSCAN; returns labels (-1 = noise).

    HDBSCAN on raw 384-d embeddings finds no density structure on small corpora
    (everything is noise), so reduce to a few PCA dimensions first and scale
    ``min_cluster_size`` down for small inputs.
    """
    import hdbscan
    from sklearn.decomposition import PCA

    n = len(X)
    dims = min(10, n - 1, X.shape[1])
    Z = PCA(n_components=dims, random_state=0).fit_transform(X) if dims >= 2 else X
    size = max(3, min(min_cluster_size, n // 25))
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=size, min_samples=2, metric="euclidean"
    )
    return clusterer.fit_predict(Z.astype(np.float64))


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

    labels = cluster_embeddings(X, min_cluster_size)

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
