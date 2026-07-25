"""pf ingest: run one source through the pipeline, or list what's registered."""

import asyncio
from typing import Annotated

import typer

from problemfinder.ingestion import pipeline
from problemfinder.sources import config
from problemfinder.sources.registry import all_sources

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    source: Annotated[str, typer.Argument(help="source key, e.g. fos_complaints")],
    limit: Annotated[int | None, typer.Option(help="stop after N work items")] = None,
    force: Annotated[bool, typer.Option(help="run even if disabled in sources.toml")] = False,
) -> None:
    """Ingest one source end to end and print the run ledger."""
    if not force and not config.is_enabled(source):
        typer.echo(f"{source} is disabled in sources.toml (use --force to override)")
        raise typer.Exit(code=1)
    record = asyncio.run(pipeline.run_source(source, limit=limit))
    typer.echo(
        f"{source}: fetched {record.fetched} payload(s), parsed {record.parsed} signal(s), "
        f"stored {record.stored_new} new, skipped {record.deduplicated} duplicate(s)"
    )
    for error in record.errors:
        typer.echo(f"  error: {error}", err=True)
    if record.errors and record.stored_new == 0:
        raise typer.Exit(code=1)


@app.command("list")
def list_sources() -> None:
    """Show every registered adapter with its method and enablement."""
    enabled = config.enabled_sources()
    for key, source in sorted(all_sources().items()):
        state = "enabled" if key in enabled else "disabled"
        typer.echo(f"{key}  v{source.version}  {source.policy.method.value}  {state}")
