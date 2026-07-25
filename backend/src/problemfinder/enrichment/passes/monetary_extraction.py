"""The largest sterling amount stated in a verbatim's own words.

Aggregates are skipped: their bodies are rendered statistics, not testimony.
The maximum is a deliberate reading: a decision usually names the disputed
sum alongside smaller incidental figures, and understatement is the safer
error for a severity proxy built on top of this field.
"""

import re
from decimal import Decimal

from problemfinder.domain.signal import ProblemSignal, VerbatimSignal
from problemfinder.enrichment.protocol import EnrichmentDraft

_AMOUNT = re.compile(r"£\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{2}))?")
_PENCE = Decimal("0.01")
_CEILING = Decimal("1e12")  # Numeric(14, 2) overflows beyond this; treat as a parse artefact


def _to_decimal(whole: str, pence: str | None) -> Decimal:
    amount = Decimal(whole.replace(",", ""))
    if pence:
        amount += Decimal(pence) * _PENCE
    return amount.quantize(_PENCE)


class MonetaryExtractionPass:
    name = "monetary_extraction"

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        if not isinstance(signal, VerbatimSignal):
            return
        amounts = [
            _to_decimal(whole, pence)
            for whole, pence in _AMOUNT.findall(f"{signal.title or ''} {signal.body}")
        ]
        credible = [amount for amount in amounts if amount < _CEILING]
        if credible:
            draft.monetary_amount = max(credible)
            draft.monetary_currency = "GBP"
