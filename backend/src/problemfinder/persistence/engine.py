"""One engine, one session factory, one context-managed unit of work."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from problemfinder.settings import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine  # noqa: PLW0603 -- single process-wide engine by design
    if _engine is None:
        _engine = create_engine(get_settings().database_url)
    return _engine


def reset_engine() -> None:
    """Drop the cached engine so the next call rereads settings. Test hook."""
    global _engine  # noqa: PLW0603 -- see get_engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


@contextmanager
def session_scope() -> Generator[Session]:
    """A transaction per unit of work: commit on success, roll back on error."""
    factory = sessionmaker(bind=get_engine())
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
