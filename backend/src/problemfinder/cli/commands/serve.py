"""pf serve: long-running processes. The worker variant lands in phase 3."""

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
