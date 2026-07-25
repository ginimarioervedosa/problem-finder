"""Signal listing and detail. Thin: parse params, call the query service."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from problemfinder.api.dependencies import FiltersDep, SessionDep
from problemfinder.api.responses import SignalPage
from problemfinder.domain.signal import AggregateSignal, VerbatimSignal
from problemfinder.queries.signal_search import get_signal, search_signals

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
def list_signals(
    session: SessionDep,
    filters: FiltersDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SignalPage:
    items, total = search_signals(session, filters, limit=limit, offset=offset)
    return SignalPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{signal_id}")
def signal_detail(signal_id: str, session: SessionDep) -> VerbatimSignal | AggregateSignal:
    signal = get_signal(session, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="no such signal")
    return signal
