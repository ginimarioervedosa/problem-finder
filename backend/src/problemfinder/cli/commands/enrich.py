"""pf enrich: derived attributes, rebuilt from stored signals on demand."""

from typing import Annotated

import typer

from problemfinder.enrichment.run import run_enrichment

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    recompute: Annotated[
        bool,
        typer.Option(
            "--recompute", help="Re-derive every signal's attributes, not just the unenriched"
        ),
    ] = False,
) -> None:
    """Run the deterministic rule passes over every stored signal."""
    report = run_enrichment(recompute=recompute)
    typer.echo(
        f"computed {report.processed} signal(s): {report.written} new version(s) written, "
        f"{report.unchanged} unchanged, {report.skipped} skipped (already enriched)"
    )
