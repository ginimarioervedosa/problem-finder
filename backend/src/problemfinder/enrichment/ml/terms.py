"""Distinctive terms per cluster, in plain Python on purpose.

The scoring is class-based TF-IDF in miniature: a term earns a cluster's
term frequency damped by how many other clusters also use it, and a term
every cluster uses scores exactly zero, so corpus boilerplate ("complaint",
"ombudsman") rules itself out without a domain stopword list. With a single
cluster there is no contrast to score, so raw frequency stands in.
Explainable by inspection, testable with no ML installed.
"""

import re
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from math import log

_WORD = re.compile(r"[a-z][a-z'-]{2,}")
_STOPWORDS = frozenset({
    "the", "and", "for", "that", "with", "was", "had", "has", "have", "this",
    "they", "their", "she", "her", "his", "him", "not", "but", "from", "would",
    "could", "should", "been", "were", "are", "all", "any", "our", "you", "your",
    "when", "what", "which", "where", "there", "about", "because", "did", "does",
    "don't", "didn't", "its", "it's", "who", "whom", "will", "can", "may", "might",
    "than", "then", "them", "these", "those", "said", "say", "also", "more", "most",
    "some", "such", "into", "out", "over", "under", "after", "before", "between",
    "just", "only", "very", "much",
})  # fmt: skip


def distinctive_terms(
    docs_by_cluster: Mapping[int, Sequence[str]], top: int = 8
) -> dict[int, tuple[str, ...]]:
    """The `top` highest-scoring terms per cluster, most distinctive first."""
    frequencies = {key: Counter(_tokens(" ".join(docs))) for key, docs in docs_by_cluster.items()}
    cluster_count = len(frequencies)
    document_frequency = Counter(term for counter in frequencies.values() for term in counter)
    return {
        key: _top_terms(counter, document_frequency, cluster_count, top)
        for key, counter in frequencies.items()
    }


def label_from_terms(terms: Sequence[str], words: int = 3) -> str:
    return "_".join(terms[:words])


def _tokens(text: str) -> Iterator[str]:
    for match in _WORD.finditer(text.casefold()):
        if match.group() not in _STOPWORDS:
            yield match.group()


def _top_terms(
    counter: Counter[str], document_frequency: Counter[str], cluster_count: int, top: int
) -> tuple[str, ...]:
    def score(term: str) -> float:
        if cluster_count == 1:
            return float(counter[term])
        return counter[term] * log(cluster_count / document_frequency[term])

    ranked = sorted(counter, key=lambda term: (-score(term), term))
    return tuple(ranked[:top])
