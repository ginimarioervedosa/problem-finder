"""Density clustering over embeddings: normalise, reduce, HDBSCAN.

Embeddings are L2-normalised so euclidean distance tracks cosine, reduced
with PCA because HDBSCAN degrades in hundreds of dimensions, then clustered.
The label -1 is HDBSCAN's noise bucket: signals that belong to no dense
cluster, deliberately left unproposed. Every step is deterministic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from problemfinder.enrichment.ml.optional import MlExtrasMissingError

if TYPE_CHECKING:
    import numpy as np

_PCA_COMPONENTS = 50


def cluster_embeddings(matrix: np.ndarray, *, min_cluster_size: int = 15) -> list[int]:
    """One cluster label per row; -1 marks noise."""
    try:
        from sklearn.cluster import HDBSCAN
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import normalize
    except ImportError as error:
        raise MlExtrasMissingError("scikit-learn") from error

    components = min(_PCA_COMPONENTS, matrix.shape[0], matrix.shape[1])
    reduced = PCA(n_components=components, random_state=0).fit_transform(normalize(matrix))
    labels = HDBSCAN(min_cluster_size=min_cluster_size).fit_predict(reduced)
    return [int(label) for label in labels]


def representative_indices(
    matrix: np.ndarray, labels: list[int], per_cluster: int = 3
) -> dict[int, list[int]]:
    """The rows nearest each cluster's centroid: its most typical members."""
    import numpy as np  # ml extras; lazy so the core install imports cleanly

    representatives: dict[int, list[int]] = {}
    for key in sorted(set(labels) - {-1}):
        indices = np.flatnonzero(np.asarray(labels) == key)
        centroid = matrix[indices].mean(axis=0)
        distances = np.linalg.norm(matrix[indices] - centroid, axis=1)
        nearest = indices[np.argsort(distances)][:per_cluster]
        representatives[key] = [int(index) for index in nearest]
    return representatives
