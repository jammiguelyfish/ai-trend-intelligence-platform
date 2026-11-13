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


def test_label_clusters_prefers_distinctive_phrases_over_common_words():
    from backend.app.pipelines.topics import label_clusters
    from backend.app.pipelines.trends import _terms

    img = ["diffusion model image generation", "image generation with diffusion model"] * 3
    llm = ["llm agents tool use", "agents call tool use llm"] * 3
    docs = [_terms(t + " model") for t in img + llm]
    labels = [0] * 6 + [1] * 6
    kw = label_clusters(docs, labels)
    assert "diffusion model" in kw[0] or "image generation" in kw[0]
    assert "model" not in kw[0][:2]  # shared by every doc, so not distinctive
    assert any("agents" in k or "llm" in k for k in kw[1][:3])
