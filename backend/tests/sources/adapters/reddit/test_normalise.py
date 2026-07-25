"""Field mapping, deterministic ids, and the link-post body fallback."""

from datetime import UTC, datetime

import pytest

from problemfinder.domain.identity import signal_id_for
from problemfinder.sources.adapters.reddit.normalise import to_signal
from problemfinder.sources.adapters.reddit.parser import parse_listing
from problemfinder.sources.protocol import ParsedRecord
from tests.sources.adapters.reddit.test_parser import FIXTURE, make_raw
from tests.support.builders import build_provenance

PROVENANCE = build_provenance()


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_listing(make_raw(FIXTURE.read_bytes())))


def test_field_mapping_and_deterministic_id(records: list[ParsedRecord]) -> None:
    signal = to_signal("reddit", records[0], PROVENANCE)
    assert signal.id == signal_id_for("reddit", "t3_1abcd01")
    assert signal.external_id == "t3_1abcd01"
    assert str(signal.url) == (
        "https://www.reddit.com/r/HENRYUK/comments/1abcd01/"
        "private_bank_froze_my_account_midcompletion/"
    )
    assert signal.published_at == datetime.fromtimestamp(1753380000.0, tz=UTC)
    assert signal.retrieved_at == PROVENANCE.fetched_at
    assert signal.author_handle == "throwaway_hnw"
    assert signal.body.startswith("Exchanged on a property purchase")
    assert signal.extras == {"subreddit": "HENRYUK", "score": 187, "num_comments": 64}


def test_link_post_body_falls_back_to_the_title(records: list[ParsedRecord]) -> None:
    signal = to_signal("reddit", records[1], PROVENANCE)
    assert signal.body == "SIPP transfer stuck for 11 weeks, provider blames the ceding scheme"
    assert signal.title == signal.body
