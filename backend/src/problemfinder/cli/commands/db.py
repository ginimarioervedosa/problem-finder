"""pf db: Alembic operations without leaving the one CLI."""

from typing import Annotated

import typer
from alembic import command
from alembic.config import Config

from problemfinder.settings import REPO_ROOT

app = typer.Typer(no_args_is_help=True)


def _config() -> Config:
    return Config(str(REPO_ROOT / "backend" / "alembic.ini"))


@app.command()
def upgrade(revision: Annotated[str, typer.Argument()] = "head") -> None:
    """Apply migrations up to the given revision."""
    command.upgrade(_config(), revision)


@app.command()
def revision(message: Annotated[str, typer.Option("-m", "--message")]) -> None:
    """Autogenerate a new migration from ORM changes."""
    command.revision(_config(), message=message, autogenerate=True)
