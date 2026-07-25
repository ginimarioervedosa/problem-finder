"""The compliance gate: lawfulness enforced in code, not judgement per session.

Runs before any adapter executes. Refusals are hard errors; there is no
override flag on purpose. A smaller lawful corpus beats a larger risky one.
"""

from datetime import UTC, date, datetime

from problemfinder.domain.source_policy import IngestionMethod, RobotsStatus, SourcePolicy

MAX_TERMS_AGE_DAYS = 365
_AUTOMATED_HTTP = {IngestionMethod.SCRAPE, IngestionMethod.BULK_DOWNLOAD}


class ComplianceError(RuntimeError):
    """The adapter's declared policy fails the gate; the run is refused."""


def check(policy: SourcePolicy, today: date | None = None) -> None:
    today = today or datetime.now(tz=UTC).date()
    if policy.method is IngestionMethod.SCRAPE and policy.robots_status is not RobotsStatus.ALLOWED:
        raise ComplianceError(
            "scraping requires an explicit robots.txt ALLOWED status; "
            f"declared {policy.robots_status}"
        )
    if policy.method in _AUTOMATED_HTTP and policy.robots_status is RobotsStatus.DISALLOWED:
        raise ComplianceError("robots.txt disallows automated collection for this source")
    age = (today - policy.terms_reviewed).days
    if age > MAX_TERMS_AGE_DAYS:
        raise ComplianceError(
            f"terms review is {age} days old (limit {MAX_TERMS_AGE_DAYS}); re-read the "
            "source's robots.txt and terms, then update the policy declaration"
        )
    if "problem-finder" not in policy.user_agent or "@" not in policy.user_agent:
        raise ComplianceError("user agent must identify the client and carry a contact address")
