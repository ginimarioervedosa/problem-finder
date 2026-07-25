"""The mechanical gate keeping domain models and ORM columns in lockstep.

The domain is canonical; the table flattens provenance into four columns and
adds dedupe_hash. Any other divergence between the two representations is a
failure here, which is how the single-source-of-truth rule survives contact
with a hand-written ORM.
"""

from types import NoneType
from typing import get_args

from pydantic import BaseModel

from problemfinder.domain.raw_payload import RawPayloadMeta
from problemfinder.domain.signal import AggregateSignal, SignalCore, VerbatimSignal
from problemfinder.persistence.orm import RawPayloadRow, SignalRow

PROVENANCE_COLUMNS = {"raw_payload_sha256", "adapter_version", "ingestion_run_id", "fetched_at"}
PERSISTENCE_ONLY_COLUMNS = {"dedupe_hash"}


def domain_field_names(*models: type[BaseModel]) -> set[str]:
    return {name for model in models for name in model.model_fields}


def is_optional(model: type[BaseModel], field: str) -> bool:
    return NoneType in get_args(model.model_fields[field].annotation)


def test_signal_columns_equal_domain_fields_plus_flattened_provenance() -> None:
    expected = (
        domain_field_names(VerbatimSignal, AggregateSignal) - {"provenance"}
        | PROVENANCE_COLUMNS
        | PERSISTENCE_ONLY_COLUMNS
    )
    actual = {column.name for column in SignalRow.__table__.columns}
    assert actual == expected


def test_core_field_optionality_matches_column_nullability() -> None:
    core_fields = set(SignalCore.model_fields) - {"provenance"}
    for name in core_fields:
        column = SignalRow.__table__.columns[name]
        assert column.nullable == is_optional(SignalCore, name), name


def test_variant_specific_fields_are_nullable_columns() -> None:
    variant_fields = (
        domain_field_names(VerbatimSignal, AggregateSignal)
        - set(SignalCore.model_fields)
        - {"kind"}
    )
    for name in variant_fields:
        assert SignalRow.__table__.columns[name].nullable, name


def test_raw_payload_columns_equal_meta_fields() -> None:
    actual = {column.name for column in RawPayloadRow.__table__.columns}
    assert actual == set(RawPayloadMeta.model_fields)
