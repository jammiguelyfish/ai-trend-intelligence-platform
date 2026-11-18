"""Topic clustering with k-means over recent document embeddings."""
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

MISC_LABEL = "Miscellaneous"
# Mean similarity to the cluster centre below which a cluster is a grab bag
# rather than a topic. On the sample data, real topics sit at 0.46-0.71 and the
# grab bags (mostly title-only Hacker News posts) at 0.30-0.37.
MIN_COHESION = 0.4


def cluster_embeddings(
    X: np.ndarray, docs_per_topic: int = 50, max_topics: int = 20
) -> np.ndarray:
    """Group unit-norm embeddings into topics with k-means; returns a label per row.

    Density clustering (HDBSCAN) was tried first and does not suit this data:
    on ~700 mixed AI/dev posts it put 80% of them in one blob, or, tuned finer,
    marked 70% as noise. K-means assigns every document and yields readable
    topics. The silhouette score is flat across k here (~0.08), so it cannot
    pick k; one topic per ``docs_per_topic`` documents is used instead.
    """
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    n = len(X)
    k = max(2, min(max_topics, round(n / docs_per_topic), n))
    dims = min(30, n - 1, X.shape[1])
    Z = PCA(n_components=dims, random_state=0).fit_transform(X) if dims >= 2 else X
    return KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(Z)


def label_clusters(
    doc_terms: Sequence[Sequence[str]],
    labels: Sequence[int],
    top_n: int = 8,
    min_lift: float = 2.0,
) -> Dict[int, List[str]]:
    """Distinctive keywords per cluster (TF-IDF over clusters).

    A term scores high when it appears in many documents of the cluster but in
    few documents overall, so corpus-wide words ("model") lose to what actually
    sets the cluster apart ("diffusion model", "image generation").

    A term must also be at least ``min_lift`` times more common inside the
    cluster than in the whole corpus. Without this, filler such as "user",
    "system" or "building" slips in when the cluster has nothing sharper.
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
                if c >= need and (c / len(members)) * n / global_df[term] >= min_lift
            }
        )
        kept = _prune_subsumed(scored, min_phrase=0)
        out[cid] = [w for w, _ in kept.most_common(top_n)]
    return out


def merge_incoherent(
    labels: Sequence[int], sims: Sequence[float], min_cohesion: float = MIN_COHESION
):
    """Fold clusters that are not tight around their centre into one grab bag.

    Returns ``(labels, misc_id)``; ``misc_id`` is None when every cluster is
    coherent. Short, title-only posts embed poorly and k-means gathers them into
    several loose clusters that no keyword can describe; one honest
    "Miscellaneous" topic is clearer than several mislabelled ones.
    """
    labels = np.asarray(labels)
    sims = np.asarray(sims)
    loose = [
        c
        for c in sorted(set(labels.tolist()) - {-1})
        if sims[labels == c].mean() < min_cohesion
    ]
    if not loose:
        return labels, None
    misc_id = int(labels.max()) + 1
    merged = labels.copy()
    merged[np.isin(labels, loose)] = misc_id
    return merged, misc_id


def centroid_scores(X: np.ndarray, labels: Sequence[int]) -> np.ndarray:
    """Cosine similarity of each document to its cluster centre (0 for noise).

    Used to pick the headlines that best represent a topic.
    """
    labels = np.asarray(labels)
    scores = np.zeros(len(labels))
    for cid in set(labels.tolist()) - {-1}:
        idx = np.where(labels == cid)[0]
        centre = X[idx].mean(axis=0)
        centre /= np.linalg.norm(centre) or 1.0
        scores[idx] = X[idx] @ centre
    return scores


async def cluster_topics(
    session: AsyncSession, max_docs: int = 1000, min_docs: int = 10
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
    if len(docs) < min_docs:
        log.info("topics.too_few", n=len(docs))
        return []

    texts = [f"{d.title}\n{d.content or ''}" for d in docs]
    X = embed_texts(texts)

    labels = cluster_embeddings(X)

    # reset topic data
    await session.execute(delete(DocumentTopic))
    await session.execute(delete(Topic))

    doc_terms = [_terms(t) for t in texts]
    sims = centroid_scores(X, labels)
    labels, misc_id = merge_incoherent(labels, sims)
    keywords_by_cluster = label_clusters(doc_terms, labels)

    out: List[Topic] = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        members = [(d, float(s)) for d, l, s in zip(docs, labels, sims) if l == cid]
        keywords = keywords_by_cluster.get(cid, [])
        label = (
            MISC_LABEL if cid == misc_id else ", ".join(keywords[:3]) or f"topic-{cid}"
        )
        topic = Topic(
            label=label[:256],
            keywords=", ".join(keywords)[:1024],
            size=len(members),
        )
        session.add(topic)
        await session.flush()
        for m, s in members:
            session.add(DocumentTopic(document_id=m.id, topic_id=topic.id, score=s))
        out.append(topic)

    await session.commit()
    log.info("topics.done", clusters=len(out))
    _ = store  # ensure import preserved for side-effect free linter
    return out
