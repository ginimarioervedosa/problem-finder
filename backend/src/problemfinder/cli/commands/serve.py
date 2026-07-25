"""pf serve: long-running processes, the API server and the ingestion worker."""

import subprocess
import sys

import typer
import uvicorn

from problemfinder.settings import get_settings

app = typer.Typer(no_args_is_help=True)


@app.command()
def api(reload: bool = False) -> None:
    """Run the FastAPI server."""
    uvicorn.run(
        "problemfinder.api.app:create_app",
        factory=True,
        port=get_settings().api_port,
        reload=reload,
    )


@app.command()
def worker() -> None:
    """Run cron-scheduled ingests from sources.toml until interrupted.

    The worker is a sibling layer the CLI must not import, so it runs as
    `python -m problemfinder.worker` in a subprocess.
    """
    command = [sys.executable, "-m", "problemfinder.worker"]
    raise typer.Exit(code=subprocess.run(command, check=False).returncode)
