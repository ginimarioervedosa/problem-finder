"""ParsedRecord -> VerbatimSignal: one review in the reviewer's own words."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import text_field

_REVIEWS_URL_TEMPLATE = "https://apps.apple.com/{country}/app/id{app_id}?see-all=reviews"


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
    fields = record.fields
    firm = text_field(fields, "firm")
    rating = text_field(fields, "rating")
    country = text_field(fields, "country") or "gb"
    app_id = text_field(fields, "app_id") or ""
    title = text_field(fields, "title")
    return VerbatimSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=_REVIEWS_URL_TEMPLATE.format(country=country, app_id=app_id),
        published_at=_published(text_field(fields, "updated")),
        retrieved_at=provenance.fetched_at,
        title=f"{firm} App Store review: {title}" if firm and title else title,
        body=text_field(fields, "content") or "",
        firm_name=firm,
        category=None,  # reviews carry no product-group dimension
        author_handle=text_field(fields, "author"),
        extras={
            "rating": int(rating) if rating and rating.isdigit() else None,
            "app_version": text_field(fields, "app_version"),
            "vote_count": text_field(fields, "vote_count"),
            "app_id": app_id,
            "country": country,
            "review_id": text_field(fields, "review_id"),
        },
        provenance=provenance,
    )


def _published(stamp: str | None) -> datetime | None:
    if stamp is None:
        return None
    try:
        return datetime.fromisoformat(stamp).astimezone(UTC)
    except ValueError:
        return None
