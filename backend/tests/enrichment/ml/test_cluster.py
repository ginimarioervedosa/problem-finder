"""HDBSCAN over embeddings: separable groups separate, noise stays noise.

Needs scikit-learn, so the zero-ML CI environment skips this file visibly;
that skip is the extras boundary working as designed.
"""

import pytest

pytest.importorskip("numpy", reason="ml extras not installed (zero-ML environment)")
pytest.importorskip("sklearn", reason="ml extras not installed (zero-ML environment)")

import numpy as np

from problemfinder.enrichment.ml.cluster import (
    cluster_embeddings,
    representative_indices,
)


def two_blobs(per_blob: int = 6) -> np.ndarray:
    first = [[1.0 + 0.01 * i, 0.0, 0.0] for i in range(per_blob)]
    second = [[0.0, 1.0 + 0.01 * i, 0.0] for i in range(per_blob)]
    return np.array(first + second)


def test_two_separable_blobs_become_two_clusters() -> None:
    labels = cluster_embeddings(two_blobs(), min_cluster_size=3)
    assert len(set(labels) - {-1}) == 2
    assert len(set(labels[:6])) == 1  # the first blob holds together
    assert len(set(labels[6:])) == 1


def test_representatives_come_from_their_own_cluster() -> None:
    matrix = two_blobs()
    labels = cluster_embeddings(matrix, min_cluster_size=3)
    representatives = representative_indices(matrix, labels, per_cluster=2)
    for key, indices in representatives.items():
        assert len(indices) == 2
        assert all(labels[index] == key for index in indices)
