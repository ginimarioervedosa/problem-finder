"""Registration, lookup, and the unknown-key failure mode."""

import pytest

from problemfinder.sources import registry
from problemfinder.sources.protocol import Source
from tests.support.stub_source import StubSource


def test_register_indexes_an_instance_by_key() -> None:
    registry.register(StubSource)
    try:
        instance = registry.get("stub")
        assert isinstance(instance, Source)
        assert registry.get("stub") is instance
    finally:
        del registry._registry["stub"]  # noqa: SLF001


def test_unknown_key_raises_and_names_known_keys() -> None:
    with pytest.raises(registry.UnknownSourceError, match="no source adapter"):
        registry.get("not_a_source")
