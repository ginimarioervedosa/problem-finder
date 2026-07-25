"""The adapter registers itself, passes the gate, and folds cursors per subreddit."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("reddit")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("reddit").policy)


def make_item(subreddit: str, newest: float) -> WorkItem:
    return WorkItem(
        external_id=f"r/{subreddit}:new:start",
        url=f"https://oauth.reddit.com/r/{subreddit}/new?limit=100",
        request_hints={"subreddit": subreddit, "newest_created_utc": newest},
    )


def test_cursor_fold_keeps_the_newest_post_per_subreddit() -> None:
    source = registry.get("reddit")
    previous = Cursor(
        source_key="reddit",
        state={"newest_created_utc": {"HENRYUK": 500.0, "FIREUK": 900.0}},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    done = [make_item("HENRYUK", 800.0), make_item("FIREUK", 700.0)]
    folded = source.cursor_after(previous, done)
    assert folded.state == {"newest_created_utc": {"HENRYUK": 800.0, "FIREUK": 900.0}}
