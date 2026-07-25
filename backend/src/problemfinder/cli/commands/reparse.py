"""pf reparse: regenerate a source's signals from the archive, no refetch."""

from typing import Annotated

import typer

from problemfinder.ingestion import reparse


def run(source: Annotated[str, typer.Argument(help="source key, e.g. fos_complaints")]) -> None:
    """Replay every archived payload through parse and normalise."""
    record = reparse.reparse_source(source)
    typer.echo(
        f"{source}: regenerated {record.parsed} signal(s) from the archive, "
        f"rewrote {record.stored_new}, fetched {record.fetched} (always 0 by design)"
    )
    for error in record.errors:
        typer.echo(f"  error: {error}", err=True)
    if record.errors and record.stored_new == 0:
        raise typer.Exit(code=1)
