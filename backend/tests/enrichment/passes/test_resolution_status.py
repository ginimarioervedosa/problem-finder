"""Resolution comes from the source's outcome field, mapped or UNKNOWN."""

from problemfinder.domain.enrichment import ResolutionStatus
from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.passes.resolution_status import ResolutionStatusPass
from problemfinder.enrichment.protocol import EnrichmentDraft
from tests.support.builders import build_aggregate, build_verbatim


def _resolved(signal: ProblemSignal) -> ResolutionStatus | None:
    draft = EnrichmentDraft()
    ResolutionStatusPass().apply(signal, draft)
    return draft.resolution


def test_known_outcomes_map_onto_the_enum() -> None:
    assert _resolved(build_verbatim(extras={"outcome": "Upheld"})) is ResolutionStatus.UPHELD
    assert (
        _resolved(build_verbatim(extras={"outcome": "Not upheld"})) is ResolutionStatus.NOT_UPHELD
    )


def test_unmappable_outcome_is_unknown_not_dropped() -> None:
    assert _resolved(build_verbatim(extras={"outcome": "Partially something"})) is (
        ResolutionStatus.UNKNOWN
    )


def test_missing_or_blank_outcome_stays_none() -> None:
    assert _resolved(build_verbatim()) is None
    assert _resolved(build_verbatim(extras={"outcome": "  "})) is None


def test_aggregates_stay_none() -> None:
    assert _resolved(build_aggregate(extras={"outcome": "Upheld"})) is None
