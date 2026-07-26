"""pf: every ingestion and maintenance operation, runnable from one CLI."""

import typer

from problemfinder.cli.commands import db, enrich, ingest, ml, reparse, serve

app = typer.Typer(no_args_is_help=True, help="problemfinder operations")
app.add_typer(ingest.app, name="ingest", help="Run and inspect source ingestion")
app.command("reparse")(reparse.run)
app.add_typer(enrich.app, name="enrich", help="Compute and recompute derived attributes")
app.add_typer(ml.app, name="ml", help="ML theme proposal and cluster review (ml extras)")
app.add_typer(db.app, name="db", help="Database migrations")
app.add_typer(serve.app, name="serve", help="Long-running processes")
