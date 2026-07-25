"""Theme, sub-theme and product domain, from the YAML taxonomy's rules.

The theme with the most distinct keyword hits over title + body wins; ties go
to declaration order. Aggregate bodies are formulaic so they rarely hit a
theme; they still get a product domain from their source category, which is
how they corroborate verbatim-led themes by volume and trend.
"""

from collections.abc import Sequence

from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.protocol import EnrichmentDraft
from problemfinder.enrichment.taxonomy import Taxonomy, Theme


def _hits(text: str, keywords: Sequence[str]) -> int:
    return sum(1 for keyword in keywords if keyword.casefold() in text)


class TaxonomyTaggingPass:
    name = "taxonomy_tagging"

    def __init__(self, taxonomy: Taxonomy) -> None:
        self._taxonomy = taxonomy

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        if signal.category:
            draft.product_domain = self._taxonomy.product_domains.get(signal.category)
        text = f"{signal.title or ''} {signal.body}".casefold()
        theme = self._best_theme(text)
        if theme is None:
            return
        draft.theme = theme.name
        draft.sub_theme = next(
            (sub.name for sub in theme.sub_themes if _hits(text, sub.keywords)), None
        )

    def _best_theme(self, text: str) -> Theme | None:
        best: Theme | None = None
        best_hits = 0
        for theme in self._taxonomy.themes:
            hits = _hits(text, theme.keywords)
            if hits > best_hits:  # strict: earlier declaration wins ties
                best, best_hits = theme, hits
        return best
