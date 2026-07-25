"""FastAPI dependencies: the request session and the shared filter set."""

from collections.abc import Generator
from datetime import date
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from problemfinder.domain.signal import SignalKind
from problemfinder.persistence.engine import session_scope
from problemfinder.queries.signal_search import SignalFilters


def get_session() -> Generator[Session]:
    with session_scope() as session:
        yield session


def signal_filters(  # noqa: PLR0913, PLR0917 -- one parameter per query filter, by design
    source_key: str | None = None,
    kind: SignalKind | None = None,
    firm: str | None = None,
    category: str | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
    search: str | None = None,
) -> SignalFilters:
    """The dashboard filter set, flattened into explicit query parameters."""
    return SignalFilters(
        source_key=source_key,
        kind=kind,
        firm=firm,
        category=category,
        period_from=period_from,
        period_to=period_to,
        search=search,
    )


SessionDep = Annotated[Session, Depends(get_session)]
FiltersDep = Annotated[SignalFilters, Depends(signal_filters)]
