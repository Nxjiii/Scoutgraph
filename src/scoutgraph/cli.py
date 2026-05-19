from typing import Annotated

import typer

from scoutgraph.query.sample import format_passes, load_sample_passes
from scoutgraph.sources.statsbomb import StatsBombOpenDataClient
from scoutgraph.sources.statsbomb.client import StatsBombMatchRef
from scoutgraph.sources.statsbomb.inspect import format_raw_event, get_raw_event, inspect_sample
from scoutgraph.sources.statsbomb.normalize import normalize_match, normalize_sample
from scoutgraph.storage.paths import ProjectPaths

app = typer.Typer(help="ScoutGraph backend tools.")
ingest_app = typer.Typer(help="Ingest source football data.")
inspect_app = typer.Typer(help="Inspect cached source football data.")
normalize_app = typer.Typer(help="Normalize cached source data.")
query_app = typer.Typer(help="Query normalized ScoutGraph data.")
app.add_typer(ingest_app, name="ingest")
app.add_typer(inspect_app, name="inspect")
app.add_typer(normalize_app, name="normalize")
app.add_typer(query_app, name="query")


@app.callback()
def main() -> None:
    """ScoutGraph backend command group."""


@app.command()
def info(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Print the local ScoutGraph project paths."""
    paths = ProjectPaths.from_root(root)

    typer.echo("ScoutGraph backend")
    typer.echo(f"root: {paths.root}")
    typer.echo(f"raw data: {paths.raw_data}")
    typer.echo(f"processed data: {paths.processed_data}")
    typer.echo(f"cache: {paths.cache}")


@ingest_app.command("statsbomb-sample")
def ingest_statsbomb_sample(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Download and inspect a tiny StatsBomb Open Data sample."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    summary = client.fetch_sample()

    typer.echo("StatsBomb sample ready")
    typer.echo(f"competition: {summary.competition_name} {summary.season_name}")
    typer.echo(
        "match: "
        f"{summary.home_team} {summary.home_score}-{summary.away_score} {summary.away_team}"
    )
    typer.echo(f"match id: {summary.match_id}")
    typer.echo(f"events: {summary.event_count}")
    typer.echo(f"lineup teams: {summary.lineup_team_count}")


@ingest_app.command("statsbomb-match")
def ingest_statsbomb_match(
    competition_id: Annotated[int, typer.Option(help="StatsBomb competition id.")],
    season_id: Annotated[int, typer.Option(help="StatsBomb season id.")],
    match_id: Annotated[int, typer.Option(help="StatsBomb match id.")],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Download and inspect raw files for one StatsBomb match."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    match_ref = StatsBombMatchRef(
        competition_id=competition_id,
        season_id=season_id,
        match_id=match_id,
    )
    summary = client.fetch_match(match_ref)

    typer.echo("StatsBomb match ready")
    typer.echo(f"competition: {summary.competition_name} {summary.season_name}")
    typer.echo(
        "match: "
        f"{summary.home_team} {summary.home_score}-{summary.away_score} {summary.away_team}"
    )
    typer.echo(f"match id: {summary.match_id}")
    typer.echo(f"events: {summary.event_count}")
    typer.echo(f"lineup teams: {summary.lineup_team_count}")


@inspect_app.command("statsbomb-sample")
def inspect_statsbomb_sample(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    top: Annotated[
        int,
        typer.Option(help="Number of event types to show."),
    ] = 10,
) -> None:
    """Inspect the cached raw StatsBomb sample JSON."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    summary = inspect_sample(client)

    typer.echo("StatsBomb raw sample inspection")
    typer.echo(f"events: {summary.event_count}")
    typer.echo("")
    typer.echo("event types:")
    for event_type, count in summary.event_type_counts[:top]:
        typer.echo(f"- {event_type}: {count}")

    typer.echo("")
    typer.echo("lineups:")
    for lineup in summary.lineups:
        players = ", ".join(lineup.first_players)
        typer.echo(f"- {lineup.team_name}: {lineup.player_count} players")
        typer.echo(f"  first players: {players}")

    if summary.first_pass is None:
        return

    first_pass = summary.first_pass
    typer.echo("")
    typer.echo("first pass event:")
    typer.echo(f"- event id: {first_pass.event_id}")
    typer.echo(f"- player: {first_pass.player_name}")
    typer.echo(f"- team: {first_pass.team_name}")
    typer.echo(f"- location: {first_pass.location}")
    typer.echo(f"- recipient: {first_pass.recipient_name}")
    typer.echo(f"- end location: {first_pass.end_location}")
    typer.echo(f"- outcome: {first_pass.outcome_name}")


@inspect_app.command("statsbomb-event")
def inspect_statsbomb_event(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int,
        typer.Option(help="StatsBomb match id."),
    ] = 3895302,
    event_id: Annotated[
        str | None,
        typer.Option(help="Specific StatsBomb event id to inspect."),
    ] = None,
    event_type: Annotated[
        str,
        typer.Option(help="Event type to inspect when no event id is provided."),
    ] = "Pass",
) -> None:
    """Print one raw StatsBomb event JSON object."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    event = get_raw_event(
        client,
        match_id=match_id,
        event_id=event_id,
        event_type=event_type,
    )

    typer.echo(format_raw_event(event))


@normalize_app.command("statsbomb-sample")
def normalize_statsbomb_sample(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Normalize the cached StatsBomb sample into local Parquet tables."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    normalized = normalize_sample(client)

    typer.echo("Normalized StatsBomb sample")
    for table_name, count in normalized.counts().items():
        typer.echo(f"{table_name}: {count}")


@normalize_app.command("statsbomb-match")
def normalize_statsbomb_match(
    competition_id: Annotated[int, typer.Option(help="StatsBomb competition id.")],
    season_id: Annotated[int, typer.Option(help="StatsBomb season id.")],
    match_id: Annotated[int, typer.Option(help="StatsBomb match id.")],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Normalize one cached StatsBomb match into local Parquet tables."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    match_ref = StatsBombMatchRef(
        competition_id=competition_id,
        season_id=season_id,
        match_id=match_id,
    )
    normalized = normalize_match(client, match_ref)

    typer.echo("Normalized StatsBomb match")
    for table_name, count in normalized.counts().items():
        typer.echo(f"{table_name}: {count}")


@query_app.command("sample-passes")
def query_sample_passes(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of pass rows to show."),
    ] = 10,
) -> None:
    """Show passes from the normalized StatsBomb sample."""
    paths = ProjectPaths.from_root(root)
    passes = load_sample_passes(paths, limit=limit)

    typer.echo("Sample passes")
    for line in format_passes(passes):
        typer.echo(line)
