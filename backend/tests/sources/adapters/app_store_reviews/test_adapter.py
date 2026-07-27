"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import IngestionMethod, RobotsStatus
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("app_store_reviews")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_gate_with_the_robots_disallow_recorded() -> None:
    policy = registry.get("app_store_reviews").policy
    check(policy)  # official_api is not an automated-HTTP method for the robots rule
    assert policy.method is IngestionMethod.OFFICIAL_API
    assert policy.robots_status is RobotsStatus.DISALLOWED
    assert "owner decided on 2026-07-27" in policy.terms_notes


def test_cursor_fold_keeps_the_newest_review_per_app() -> None:
    source = registry.get("app_store_reviews")
    previous = Cursor(
        source_key="app_store_reviews",
        state={"newest_review_updated": {"1052238659": "2026-07-20T00:00:00+00:00"}},
        updated_at=datetime(2026, 7, 27, tzinfo=UTC),
    )
    done = [
        WorkItem(
            external_id="gb:1052238659:page-1",
            url="https://itunes.apple.com/gb/rss/x/json",
            request_hints={"app_id": "1052238659", "newest_updated": "2026-07-25T17:17:29+00:00"},
        ),
        WorkItem(
            external_id="gb:932493382:page-1",
            url="https://itunes.apple.com/gb/rss/y/json",
            request_hints={"app_id": "932493382", "newest_updated": "2026-07-26T09:00:00+00:00"},
        ),
    ]
    folded = source.cursor_after(previous, done)
    assert folded.state == {
        "newest_review_updated": {
            "1052238659": "2026-07-25T17:17:29+00:00",
            "932493382": "2026-07-26T09:00:00+00:00",
        }
    }
