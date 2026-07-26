"""Local sentence embeddings behind a content-addressed disk cache.

Vectors are keyed by the sha256 of each text, so reclustering an unchanged
corpus never re-encodes, and edited signals re-encode exactly once. The
cache lives under the gitignored ml cache directory: derived, disposable,
rebuildable. The default encoder is all-MiniLM-L6-v2, which reads roughly
the first 256 tokens; clustering wants the gist, not the tail.
"""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from problemfinder.enrichment.ml.optional import MlExtrasMissingError

if TYPE_CHECKING:
    import numpy as np

_CACHE_FILE = "embeddings.npz"
_DEFAULT_MODEL = "all-MiniLM-L6-v2"


class Encoder(Protocol):
    """Anything that turns texts into one vector per text."""

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...


def embed_texts(
    texts: Sequence[str], cache_dir: Path, encoder: Encoder | None = None
) -> np.ndarray:
    """One row per text, cache hits first, the encoder only for the misses."""
    import numpy as np  # ml extras; lazy so the core install imports cleanly

    keys = [sha256(text.encode("utf-8")).hexdigest() for text in texts]
    cache_file = cache_dir / _CACHE_FILE
    cached = _load_cache(cache_file)
    missing = [index for index, key in enumerate(keys) if key not in cached]
    if missing:
        encoder = encoder or _default_encoder()
        vectors = encoder.encode([texts[index] for index in missing])
        for index, vector in zip(missing, vectors, strict=True):
            cached[keys[index]] = vector
        cache_dir.mkdir(parents=True, exist_ok=True)
        np.savez(
            cache_file,
            keys=np.array(list(cached), dtype=str),
            vectors=np.stack(list(cached.values())),
        )
    return np.stack([cached[key] for key in keys])


def _load_cache(cache_file: Path) -> dict[str, np.ndarray]:
    import numpy as np

    if not cache_file.exists():
        return {}
    with np.load(cache_file) as archive:
        return dict(zip(archive["keys"], archive["vectors"], strict=True))


def _default_encoder() -> Encoder:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise MlExtrasMissingError("sentence-transformers") from error
    return _SentenceTransformerEncoder(SentenceTransformer(_DEFAULT_MODEL))


class _SentenceTransformerEncoder:
    """Adapts SentenceTransformer's encode signature to the Encoder protocol."""

    def __init__(self, model: object) -> None:
        self._model = model

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        result: np.ndarray = self._model.encode(  # type: ignore[attr-defined]
            list(texts), show_progress_bar=False
        )
        return result
