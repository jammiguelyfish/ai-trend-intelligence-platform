import numpy as np

from backend.app.pipelines.topics import cluster_embeddings


def _blobs(groups=3, per_group=20, dim=384, noise=0.15, seed=0):
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(groups, dim))
    X = np.vstack(
        [c + noise * rng.normal(size=(per_group, dim)) for c in centers]
    )
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    return X


def test_cluster_embeddings_separates_distinct_groups():
    labels = cluster_embeddings(_blobs(), min_cluster_size=5)
    found = set(labels) - {-1}
    assert len(found) >= 2
    # points from the same generated group should mostly share a label
    first = labels[:20]
    assert (first == np.bincount(first[first >= 0]).argmax()).sum() >= 15


def test_cluster_embeddings_handles_tiny_input():
    labels = cluster_embeddings(_blobs(groups=1, per_group=6), min_cluster_size=5)
    assert len(labels) == 6
