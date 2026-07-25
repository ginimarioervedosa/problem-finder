"""The rules:v1 pass sequence — order is part of the contract.

Severity runs last because it reads the monetary amount and resolution the
earlier passes left on the draft. Bump RULES_METHOD when the sequence or any
pass's behaviour changes meaningfully; the method string is the audit trail
on every stored enrichment row.
"""

from problemfinder.enrichment.passes.monetary_extraction import MonetaryExtractionPass
from problemfinder.enrichment.passes.resolution_status import ResolutionStatusPass
from problemfinder.enrichment.passes.segment_inference import SegmentInferencePass
from problemfinder.enrichment.passes.severity_proxy import SeverityProxyPass
from problemfinder.enrichment.passes.taxonomy_tagging import TaxonomyTaggingPass
from problemfinder.enrichment.protocol import EnrichmentPass
from problemfinder.enrichment.taxonomy import Taxonomy

RULES_METHOD = "rules:v1"


def rules_v1(taxonomy: Taxonomy) -> tuple[EnrichmentPass, ...]:
    return (
        TaxonomyTaggingPass(taxonomy),
        MonetaryExtractionPass(),
        ResolutionStatusPass(),
        SegmentInferencePass(),
        SeverityProxyPass(),
    )
