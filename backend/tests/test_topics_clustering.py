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
    labels = cluster_embeddings(_blobs(), docs_per_topic=20)
    assert len(set(labels)) == 3
    # points from the same generated group should mostly share a label
    first = labels[:20]
    assert (first == np.bincount(first).argmax()).sum() == 20


def test_cluster_embeddings_handles_tiny_input():
    labels = cluster_embeddings(_blobs(groups=1, per_group=6))
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


def test_centroid_scores_rank_central_points_first_and_ignore_noise():
    from backend.app.pipelines.topics import centroid_scores

    X = np.array([[1.0, 0.0], [0.99, 0.14], [0.8, 0.6], [0.0, 1.0]])
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    s = centroid_scores(X, [0, 0, 0, -1])
    assert s[3] == 0.0
    assert s[1] > s[0] and s[1] > s[2]  # middle point is closest to the centre
