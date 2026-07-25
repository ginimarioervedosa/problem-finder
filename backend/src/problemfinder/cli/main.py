"""pf: every ingestion and maintenance operation, runnable from one CLI."""

import typer

from problemfinder.cli.commands import db, ingest, reparse, serve

app = typer.Typer(no_args_is_help=True, help="problemfinder operations")
app.add_typer(ingest.app, name="ingest", help="Run and inspect source ingestion")
app.command("reparse")(reparse.run)
app.add_typer(db.app, name="db", help="Database migrations")
app.add_typer(serve.app, name="serve", help="Long-running processes")
