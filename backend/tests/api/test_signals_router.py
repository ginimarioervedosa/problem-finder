"""Routers stay thin; these tests drive them over the real query layer."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from problemfinder.api.app import create_app
from problemfinder.api.dependencies import get_session
from tests.support.builders import build_aggregate, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def client(db_session: Session) -> TestClient:
    seed_signals(
        db_session,
        [
            build_aggregate(
                external_id="h1-2025:alpha:banking", firm_name="Alpha Bank", volume=100
            ),
            build_verbatim(body="my SIPP transfer stalled for months"),
        ],
    )
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    return TestClient(app)


def test_list_signals_pages_and_filters(client: TestClient) -> None:
    page = client.get("/api/signals", params={"firm": "alpha"}).json()
    assert page["total"] == 1
    assert page["items"][0]["kind"] == "aggregate"
    assert page["items"][0]["firm_name"] == "Alpha Bank"


def test_detail_round_trips_and_missing_is_404(client: TestClient) -> None:
    signal_id = client.get("/api/signals").json()["items"][0]["id"]
    assert client.get(f"/api/signals/{signal_id}").json()["id"] == signal_id
    missing = client.get("/api/signals/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404


def test_summaries_by_category(client: TestClient) -> None:
    rows = client.get("/api/summaries/category").json()
    assert {row["key"]: row["volume"] for row in rows} == {"Banking & Credit": 100}


def test_sources_lists_fos_with_policy(client: TestClient) -> None:
    sources = {entry["key"]: entry for entry in client.get("/api/sources").json()}
    assert set(sources) == {"fos_complaints", "fos_decisions"}
    fos = sources["fos_complaints"]
    assert fos["enabled"] is True
    assert fos["policy"]["method"] == "bulk_download"
    assert fos["last_run"]["source_key"] == "fos_complaints"  # seeded provenance run
