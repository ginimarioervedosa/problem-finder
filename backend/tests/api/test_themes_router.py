"""The themes router stays thin over the ranked-themes query."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from problemfinder.api.app import create_app
from problemfinder.api.dependencies import get_session
from problemfinder.persistence.repositories.signal_enrichments import append_many
from tests.support.builders import build_enrichment, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def client(db_session: Session) -> TestClient:
    signal = build_verbatim(body="an investment scam")
    seed_signals(db_session, [signal])
    append_many(db_session, [build_enrichment(signal.id, severity=0.9)])
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    return TestClient(app)


def test_ranked_themes_round_trip(client: TestClient) -> None:
    rows = client.get("/api/themes").json()
    assert len(rows) == 1
    assert rows[0]["theme"] == "fraud_and_scams"
    assert rows[0]["signals"] == 1
    assert rows[0]["severity_weighted"] == pytest.approx(0.9)


def test_theme_filter_reaches_the_signals_endpoint(client: TestClient) -> None:
    page = client.get("/api/signals", params={"theme": "fraud_and_scams"}).json()
    assert page["total"] == 1
    empty = client.get("/api/signals", params={"theme": "nothing_here"}).json()
    assert empty["total"] == 0
