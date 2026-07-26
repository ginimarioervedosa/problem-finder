"""The theme-suggestions router stays thin over the views query."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from problemfinder.api.app import create_app
from problemfinder.api.dependencies import get_session
from problemfinder.persistence.repositories.theme_suggestions import replace_proposed
from tests.support.builders import build_suggestion, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def client(db_session: Session) -> TestClient:
    signal = build_verbatim(body="A cryptocurrency scam drained the account.")
    seed_signals(db_session, [signal])
    replace_proposed(
        db_session,
        "hdbscan:v1",
        [
            build_suggestion(
                member_signal_ids=(signal.id,),
                representative_signal_ids=(signal.id,),
                size=1,
            )
        ],
    )
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    return TestClient(app)


def test_suggestions_round_trip(client: TestClient) -> None:
    rows = client.get("/api/theme-suggestions").json()
    assert len(rows) == 1
    assert rows[0]["status"] == "proposed"
    assert rows[0]["suggested_theme"] == "delays_and_service_failures"
    assert rows[0]["representatives"][0]["snippet"].startswith("A cryptocurrency scam")
    assert "member_signal_ids" not in rows[0]


def test_status_filter_is_honoured(client: TestClient) -> None:
    assert client.get("/api/theme-suggestions", params={"status": "accepted"}).json() == []
    assert client.get("/api/theme-suggestions", params={"status": "bogus"}).status_code == 422
