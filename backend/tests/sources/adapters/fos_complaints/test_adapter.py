"""The adapter registers itself and satisfies protocol and compliance gates."""

from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source


def test_registered_under_its_key() -> None:
    source = registry.get("fos_complaints")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("fos_complaints").policy)
