"""Where the taxonomy already covers a cluster, name the closest theme.

Overlap means a cluster term and a theme keyword contain one another after
casefolding, so single-word terms still hit multi-word keywords. The theme
with the most distinct keyword hits wins; ties go to declaration order,
mirroring the rules-pass priority. No hits means the cluster is genuinely
new territory, and the suggestion says so with None.
"""

from collections.abc import Sequence

from problemfinder.enrichment.taxonomy import Taxonomy


def closest_theme(terms: Sequence[str], taxonomy: Taxonomy) -> str | None:
    """The best-matching existing theme name, or None when nothing overlaps."""
    best_name: str | None = None
    best_hits = 0
    for theme in taxonomy.themes:
        hits = sum(1 for keyword in theme.keywords if _overlaps(keyword, terms))
        if hits > best_hits:
            best_name, best_hits = theme.name, hits
    return best_name


def _overlaps(keyword: str, terms: Sequence[str]) -> bool:
    folded = keyword.casefold()
    return any(term in folded or folded in term for term in (t.casefold() for t in terms))
