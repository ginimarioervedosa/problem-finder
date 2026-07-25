"""Runtime configuration, read once from the environment and repo-root .env.

Defaults match docker-compose.yml, so a fresh clone works with no .env at all.
Paths default relative to the repository root regardless of the working
directory, because the CLI runs from backend/ while data/ lives at the root.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PF_", env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://pf:pf@localhost:5432/problemfinder"
    archive_dir: Path = REPO_ROOT / "data" / "archive"
    sources_config: Path = REPO_ROOT / "backend" / "config" / "sources.toml"
    taxonomy_path: Path = REPO_ROOT / "backend" / "config" / "taxonomy.yaml"
    api_port: int = 8000
    cors_origin: str = "http://localhost:5173"
    # Reddit script-app OAuth credentials; .env only, never committed.
    reddit_client_id: str = ""
    reddit_client_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
