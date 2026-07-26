"""The embedding cache: encode each text once, replay it forever.

These tests inject a stub encoder, so no model and no network; they still
need numpy for the cache format, so the zero-ML CI environment skips them
visibly. That skip is the extras boundary working as designed, not a gap.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest

pytest.importorskip("numpy", reason="ml extras not installed (zero-ML environment)")

import numpy as np

from problemfinder.enrichment.ml.embeddings import embed_texts


class StubEncoder:
    """Deterministic vectors: text length and call count, nothing clever."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        self.calls.append(list(texts))
        return np.array([[float(len(text)), 1.0] for text in texts])


def test_vectors_come_back_one_per_text_in_order(tmp_path: Path) -> None:
    matrix = embed_texts(["ab", "abcd"], tmp_path, StubEncoder())
    assert matrix.shape == (2, 2)
    assert matrix[0][0] == 2.0
    assert matrix[1][0] == 4.0


def test_second_run_reads_the_cache_instead_of_the_encoder(tmp_path: Path) -> None:
    encoder = StubEncoder()
    embed_texts(["ab", "abcd"], tmp_path, encoder)
    matrix = embed_texts(["ab", "abcd"], tmp_path, encoder)
    assert len(encoder.calls) == 1
    assert matrix[1][0] == 4.0


def test_only_the_new_texts_reach_the_encoder(tmp_path: Path) -> None:
    encoder = StubEncoder()
    embed_texts(["ab"], tmp_path, encoder)
    embed_texts(["ab", "new text"], tmp_path, encoder)
    assert encoder.calls == [["ab"], ["new text"]]
