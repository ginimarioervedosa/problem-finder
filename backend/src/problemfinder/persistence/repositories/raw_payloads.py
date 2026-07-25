"""The database index into the on-disk raw archive."""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from problemfinder.domain.raw_payload import RawPayloadMeta
from problemfinder.persistence.orm import RawPayloadRow


def add_if_absent(session: Session, meta: RawPayloadMeta) -> bool:
    """Record archive metadata once per content hash. Returns True when new."""
    stmt = (
        insert(RawPayloadRow)
        .values(**meta.model_dump())
        .on_conflict_do_nothing(index_elements=["sha256"])
        .returning(RawPayloadRow.sha256)
    )
    return session.execute(stmt).scalar() is not None


def get(session: Session, sha256: str) -> RawPayloadMeta | None:
    row = session.get(RawPayloadRow, sha256)
    return RawPayloadMeta.model_validate(row, from_attributes=True) if row else None
