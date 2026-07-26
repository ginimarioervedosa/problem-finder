"""Shared fixtures. DB fixtures target <database>_test on the compose Postgres."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from problemfinder.persistence.engine import reset_engine
from problemfinder.persistence.orm import Base
from problemfinder.settings import get_settings


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine]:
    url = make_url(get_settings().database_url)
    test_url = url.set(database=f"{url.database}_test")
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("select 1 from pg_database where datname = :name"),
                {"name": test_url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'create database "{test_url.database}"'))
    except OperationalError:
        pytest.fail("Postgres is unavailable; db-marked tests need `make up` first")
    finally:
        admin.dispose()

    engine = create_engine(test_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session]:
    """Each test runs in a transaction that is always rolled back."""
    with db_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        yield session
        session.close()
        transaction.rollback()


@pytest.fixture
def tmp_archive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Path]:
    """Redirect the raw archive to a throwaway directory."""
    archive_dir = tmp_path / "archive"
    monkeypatch.setenv("PF_ARCHIVE_DIR", str(archive_dir))
    get_settings.cache_clear()
    yield archive_dir
    get_settings.cache_clear()


@pytest.fixture
def pipeline_db(db_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Generator[Engine]:
    """Point the process-wide engine at the test database, truncating after.

    The pipeline opens and commits its own sessions, so the rollback trick in
    db_session cannot contain it; truncation is the honest cleanup.
    """
    url = db_engine.url.render_as_string(hide_password=False)
    monkeypatch.setenv("PF_DATABASE_URL", url)
    get_settings.cache_clear()
    reset_engine()
    yield db_engine
    with db_engine.begin() as connection:
        connection.execute(
            text(
                "truncate signals, raw_payloads, ingestion_runs, cursors, theme_suggestions cascade"
            )
        )
    get_settings.cache_clear()
    reset_engine()
