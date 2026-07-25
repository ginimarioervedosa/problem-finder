"""sources.toml is the single config entry a source ships."""

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest

from problemfinder.settings import get_settings
from problemfinder.sources.config import is_enabled, schedules, source_options

CONFIG = """
[sources.on_source]
enabled = true
schedule = "0 7 * * 1"

[sources.off_source]
enabled = false
schedule = "0 7 * * 2"

[sources.on_source.options]
window_from = 2025-01-01
names = ["a", "b"]
"""


@pytest.fixture
def sources_toml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Path]:
    config = tmp_path / "sources.toml"
    config.write_text(CONFIG)
    monkeypatch.setenv("PF_SOURCES_CONFIG", str(config))
    get_settings.cache_clear()
    yield config
    get_settings.cache_clear()


def test_enabled_flag_is_respected(sources_toml: Path) -> None:
    assert is_enabled("on_source")
    assert not is_enabled("off_source")
    assert not is_enabled("absent_source")


def test_options_are_returned_verbatim_with_toml_types(sources_toml: Path) -> None:
    options = source_options("on_source")
    assert options["window_from"] == date(2025, 1, 1)
    assert options["names"] == ["a", "b"]


def test_missing_options_table_is_an_empty_mapping(sources_toml: Path) -> None:
    assert source_options("off_source") == {}
    assert source_options("absent_source") == {}


def test_schedules_cover_only_enabled_sources(sources_toml: Path) -> None:
    assert schedules() == {"on_source": "0 7 * * 1"}
