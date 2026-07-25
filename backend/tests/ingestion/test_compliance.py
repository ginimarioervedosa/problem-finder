"""Every refusal rule of the compliance gate, and one passing policy."""

from datetime import date

import pytest

from problemfinder.domain.source_policy import IngestionMethod, RobotsStatus, SourcePolicy
from problemfinder.ingestion.compliance import ComplianceError, check
from tests.support.stub_source import STUB_POLICY

TODAY = date(2026, 7, 25)


def policy(**overrides: object) -> SourcePolicy:
    base = STUB_POLICY.model_copy(
        update={"user_agent": "problem-finder/0.1 (contact: research@example.org)"}
    )
    return base.model_copy(update=dict(overrides))


def test_compliant_policy_passes() -> None:
    check(policy(), today=TODAY)


def test_scraping_requires_explicit_robots_allowed() -> None:
    scrape = policy(method=IngestionMethod.SCRAPE, robots_status=RobotsStatus.NOT_APPLICABLE)
    with pytest.raises(ComplianceError, match=r"robots\.txt ALLOWED"):
        check(scrape, today=TODAY)


def test_robots_disallowed_blocks_bulk_download_too() -> None:
    blocked = policy(robots_status=RobotsStatus.DISALLOWED)
    with pytest.raises(ComplianceError, match="disallows automated collection"):
        check(blocked, today=TODAY)


def test_stale_terms_review_is_refused() -> None:
    stale = policy(terms_reviewed=date(2025, 1, 1))
    with pytest.raises(ComplianceError, match="re-read"):
        check(stale, today=TODAY)


def test_anonymous_user_agent_is_refused() -> None:
    anonymous = policy(user_agent="Mozilla/5.0")
    with pytest.raises(ComplianceError, match="identify the client"):
        check(anonymous, today=TODAY)
