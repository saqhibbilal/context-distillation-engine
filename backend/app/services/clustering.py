"""Topic clustering on message embeddings."""

from typing import Any

import numpy as np


def cluster_embeddings(
    embeddings: list[list[float]],
    min_cluster_size: int = 2,
    min_samples: int = 1,
) -> list[int]:
    """
    Cluster embeddings using HDBSCAN.
    Returns cluster labels: -1 = noise (no cluster), 0+ = cluster id.
    """
    import hdbscan

    if not embeddings:
        return []
    X = np.array(embeddings, dtype=np.float32)
    if len(X) < 2:
        return [0] * len(X)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(X)
    return labels.tolist()


def get_cluster_summary(
    labels: list[int],
    messages: list[dict],
) -> list[dict[str, Any]]:
    """
    Group messages by cluster label and produce summaries.
    messages: list of serialized message dicts with 'content', 'author', etc.
    """
    from collections import defaultdict

    groups: dict[int, list[int]] = defaultdict(list)
    for i, lab in enumerate(labels):
        groups[lab].append(i)

    clusters = []
    for label, indices in sorted(groups.items(), key=lambda x: -len(x[1])):
        if label == -1:
            topic_name = "Unclustered"
        else:
            topic_name = f"Topic {label}"
        msg_list = [messages[i] for i in indices]
        clusters.append(
            {
                "topic_id": label,
                "topic_name": topic_name,
                "message_indices": indices,
                "message_count": len(indices),
                "messages": msg_list,
            }
        )
    return clusters
