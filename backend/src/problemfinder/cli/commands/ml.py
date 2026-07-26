"""pf ml: cluster the verbatims, then review what the clusters propose."""

from collections.abc import Callable
from typing import Annotated

import typer

from problemfinder.domain.theme_suggestion import SuggestionStatus, ThemeSuggestion
from problemfinder.enrichment.ml import review
from problemfinder.enrichment.ml.optional import MlExtrasMissingError
from problemfinder.enrichment.ml.suggest import propose_themes

app = typer.Typer(no_args_is_help=True)


@app.command()
def cluster(
    min_cluster_size: Annotated[
        int, typer.Option("--min-cluster-size", min=2, help="Smallest cluster worth proposing")
    ] = 30,
) -> None:
    """Embed every verbatim signal and propose candidate themes."""
    try:
        report = propose_themes(min_cluster_size=min_cluster_size)
    except MlExtrasMissingError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(
        f"clustered {report.verbatims} verbatim(s) into {report.clusters} proposal(s) "
        f"({report.noise} left as noise); {report.replaced} earlier proposal(s) replaced"
    )


@app.command()
def suggestions(
    status: Annotated[
        SuggestionStatus | None, typer.Option("--status", help="Show one status only")
    ] = None,
) -> None:
    """List theme suggestions and their review state."""
    rows = review.list_reviews(status)
    if not rows:
        typer.echo("no suggestions; run `pf ml cluster` first")
        return
    for suggestion in rows:
        typer.echo(_describe(suggestion))


@app.command()
def accept(
    cluster_key: Annotated[int, typer.Argument(help="Cluster key from `pf ml suggestions`")],
    theme: Annotated[
        str | None,
        typer.Option("--theme", help="Theme to map onto (default: the suggested match)"),
    ] = None,
) -> None:
    """Map one proposed cluster onto a theme."""
    decided = _decide(review.accept, cluster_key, theme)
    typer.echo(
        f"cluster {decided.cluster_key} accepted as '{decided.mapped_theme}'; "
        "run `pf enrich run --recompute` to carry it into enrichment"
    )


@app.command()
def reject(
    cluster_key: Annotated[int, typer.Argument(help="Cluster key from `pf ml suggestions`")],
) -> None:
    """Retire one proposed cluster."""
    decided = _decide(review.reject, cluster_key)
    typer.echo(f"cluster {decided.cluster_key} rejected")


def _decide(
    action: Callable[..., ThemeSuggestion], cluster_key: int, *args: str | None
) -> ThemeSuggestion:
    try:
        return action(cluster_key, *args)
    except review.UnknownClusterError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(code=1) from error


def _describe(suggestion: ThemeSuggestion) -> str:
    mapped = f" -> {suggestion.mapped_theme}" if suggestion.mapped_theme else ""
    suggested = suggestion.suggested_theme or "new territory"
    return (
        f"[{suggestion.status.value}{mapped}] cluster {suggestion.cluster_key}: "
        f"{suggestion.label} ({suggestion.size} signals, suggests: {suggested}) "
        f"terms: {', '.join(suggestion.top_terms[:5])}"
    )
