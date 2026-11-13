"""Topic clustering using HDBSCAN over recent document embeddings."""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Sequence

import numpy as np
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.embeddings import store
from backend.app.embeddings.model import embed_texts
from backend.app.models import Document, DocumentTopic, Topic
from backend.app.pipelines.trends import _prune_subsumed, _terms
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


def label_clusters(
    doc_terms: Sequence[Sequence[str]], labels: Sequence[int], top_n: int = 8
) -> Dict[int, List[str]]:
    """Distinctive keywords per cluster (TF-IDF over clusters).

    A term scores high when it appears in many documents of the cluster but in
    few documents overall, so corpus-wide words ("model") lose to what actually
    sets the cluster apart ("diffusion model", "image generation").
    """
    n = len(doc_terms)
    global_df: Counter = Counter()
    for terms in doc_terms:
        global_df.update(set(terms))

    out: Dict[int, List[str]] = {}
    for cid in sorted(set(labels) - {-1}):
        members = [t for t, l in zip(doc_terms, labels) if l == cid]
        df: Counter = Counter()
        for terms in members:
            df.update(set(terms))
        need = max(2, min(len(members) // 5, 4))
        scored = Counter(
            {
                term: (c / len(members)) * math.log(1 + n / global_df[term])
                for term, c in df.items()
                if c >= need
            }
        )
        kept = _prune_subsumed(scored, min_phrase=0)
        out[cid] = [w for w, _ in kept.most_common(top_n)]
    return out


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

    doc_terms = [_terms(t) for t in texts]
    keywords_by_cluster = label_clusters(doc_terms, labels)

    out: List[Topic] = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        members = [d for d, l in zip(docs, labels) if l == cid]
        keywords = keywords_by_cluster.get(cid, [])
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
