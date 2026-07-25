"""Run invariants: recompute idempotence, versioning, audit columns."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, select

from problemfinder.enrichment.run import run_enrichment
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.orm import SignalEnrichmentRow
from problemfinder.settings import get_settings
from tests.support.builders import build_aggregate, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db

TAXONOMY_V1 = """
product_domains:
  "Banking & Credit": banking_and_credit
themes:
  - name: fraud_and_scams
    keywords: [scam]
    sub_themes:
      - name: investment_scam
        keywords: ["investment scam"]
"""
# Same rules, one opinion changed: the theme was renamed.
TAXONOMY_V2 = TAXONOMY_V1.replace("fraud_and_scams", "scams_reworded")


@pytest.fixture
def enrichment_db(
    pipeline_db: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[Engine, Path]]:
    taxonomy_path = tmp_path / "taxonomy.yaml"
    taxonomy_path.write_text(TAXONOMY_V1)
    monkeypatch.setenv("PF_TAXONOMY_PATH", str(taxonomy_path))
    get_settings.cache_clear()
    with session_scope() as session:
        seed_signals(
            session,
            [
                build_verbatim(
                    body="An investment scam took £45,000.", extras={"outcome": "Upheld"}
                ),
                build_aggregate(upheld_share=0.25),
            ],
        )
    yield pipeline_db, taxonomy_path


def test_recompute_is_idempotent_in_one_command(enrichment_db: tuple[Engine, Path]) -> None:
    first = run_enrichment(recompute=True)
    assert (first.processed, first.written, first.unchanged) == (2, 2, 0)

    second = run_enrichment(recompute=True)
    assert (second.processed, second.written, second.unchanged) == (2, 0, 2)


def test_plain_run_only_touches_the_unenriched(enrichment_db: tuple[Engine, Path]) -> None:
    run_enrichment()
    report = run_enrichment()
    assert (report.processed, report.written, report.skipped) == (0, 0, 2)


def test_every_row_carries_method_and_version(enrichment_db: tuple[Engine, Path]) -> None:
    run_enrichment()
    engine, _ = enrichment_db
    with engine.connect() as connection:
        rows = connection.execute(
            select(
                SignalEnrichmentRow.version,
                SignalEnrichmentRow.method,
                SignalEnrichmentRow.theme,
                SignalEnrichmentRow.severity_basis,
            )
        ).fetchall()
    assert len(rows) == 2
    assert all(row.version == 1 and row.method == "rules:v1" for row in rows)
    themes = {row.theme for row in rows}
    assert "fraud_and_scams" in themes  # the verbatim
    assert None in themes  # the aggregate: domain from category, no theme


def test_changed_rules_append_a_new_version_for_affected_signals(
    enrichment_db: tuple[Engine, Path],
) -> None:
    engine, taxonomy_path = enrichment_db
    run_enrichment()
    taxonomy_path.write_text(TAXONOMY_V2)

    report = run_enrichment(recompute=True)
    assert report.written == 1  # only the verbatim's theme changed
    assert report.unchanged == 1

    with engine.connect() as connection:
        latest = connection.execute(
            select(SignalEnrichmentRow.theme)
            .where(SignalEnrichmentRow.theme.is_not(None))
            .order_by(SignalEnrichmentRow.version.desc())
            .limit(1)
        ).scalar_one()
    assert latest == "scams_reworded"
