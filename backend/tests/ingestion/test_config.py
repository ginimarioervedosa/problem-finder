"""sources.toml is the single config entry a source ships."""

from collections.abc import Generator
from pathlib import Path

import pytest

from problemfinder.ingestion.config import is_enabled
from problemfinder.settings import get_settings


@pytest.fixture
def sources_toml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Path]:
    config = tmp_path / "sources.toml"
    config.write_text(
        "[sources.on_source]\nenabled = true\n\n[sources.off_source]\nenabled = false\n"
    )
    monkeypatch.setenv("PF_SOURCES_CONFIG", str(config))
    get_settings.cache_clear()
    yield config
    get_settings.cache_clear()


def test_enabled_flag_is_respected(sources_toml: Path) -> None:
    assert is_enabled("on_source")
    assert not is_enabled("off_source")
    assert not is_enabled("absent_source")
