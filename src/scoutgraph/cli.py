from typing import Annotated

import typer

from scoutgraph.features.player_passing import (
    build_player_passing_features,
    format_player_passing_features,
)
from scoutgraph.features.player_carrying import (
    build_player_carrying_features,
    format_player_carrying_features,
)
from scoutgraph.features.player_shooting import (
    build_player_shooting_features,
    format_player_shooting_features,
)
from scoutgraph.features.player_matrix import (
    build_player_feature_matrix,
    format_player_feature_matrix,
)
from scoutgraph.features.team_matrix import build_team_feature_matrix, format_team_feature_matrix
from scoutgraph.features.sanity import (
    format_feature_inspection,
    inspect_player_vector,
    inspect_team_vector,
)
from scoutgraph.query.sample import format_passes, load_passes, load_sample_passes
from scoutgraph.similarity.player_similarity import (
    explain_similar_players,
    find_similar_players,
    format_similar_players,
    format_similar_players_with_explanations,
)
from scoutgraph.sources.statsbomb import StatsBombOpenDataClient
from scoutgraph.sources.statsbomb.client import StatsBombMatchRef
from scoutgraph.sources.statsbomb.discovery import (
    format_competition_option,
    format_match_option,
    list_competitions,
    list_matches,
)
from scoutgraph.sources.statsbomb.inspect import format_raw_event, get_raw_event, inspect_sample
from scoutgraph.sources.statsbomb.normalize import normalize_match, normalize_sample, normalize_season
from scoutgraph.storage.paths import ProjectPaths

app = typer.Typer(help="Football data ingestion, inspection, normalization, and query tools.")
ingest_app = typer.Typer(help="Download raw football data into the local cache.")
inspect_app = typer.Typer(help="Inspect cached raw football data.")
normalize_app = typer.Typer(help="Convert cached raw data into analytical tables.")
query_app = typer.Typer(help="Query normalized ScoutGraph tables.")
list_app = typer.Typer(help="Discover available source competitions and matches.")
features_app = typer.Typer(help="Build derived player and team feature tables.")
similarity_app = typer.Typer(help="Find similar players and teams from feature tables.")
app.add_typer(ingest_app, name="ingest")
app.add_typer(inspect_app, name="inspect")
app.add_typer(normalize_app, name="normalize")
app.add_typer(query_app, name="query")
app.add_typer(list_app, name="list")
app.add_typer(features_app, name="features")
app.add_typer(similarity_app, name="similarity")


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


@ingest_app.command("statsbomb-season")
def ingest_statsbomb_season(
    competition_id: Annotated[int, typer.Option(help="StatsBomb competition id.")],
    season_id: Annotated[int, typer.Option(help="StatsBomb season id.")],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(help="Maximum number of matches to cache."),
    ] = None,
) -> None:
    """Download raw files for a StatsBomb competition-season."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    summary = client.fetch_season(
        competition_id=competition_id,
        season_id=season_id,
        limit=limit,
    )

    typer.echo("StatsBomb season ready")
    typer.echo(f"competition: {summary.competition_name} {summary.season_name}")
    typer.echo(f"competition id: {summary.competition_id}")
    typer.echo(f"season id: {summary.season_id}")
    typer.echo(f"matches cached: {summary.match_count}")
    typer.echo(f"match ids: {', '.join(str(match_id) for match_id in summary.match_ids)}")


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


@inspect_app.command("player-vector")
def inspect_player_feature_vector(
    player: Annotated[
        str,
        typer.Option(help="Player name or unique partial player name to inspect."),
    ],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Inspect one generated player feature vector."""
    inspection = inspect_player_vector(ProjectPaths.from_root(root), player=player)
    for line in format_feature_inspection(inspection):
        typer.echo(line)


@inspect_app.command("team-vector")
def inspect_team_feature_vector(
    team: Annotated[
        str,
        typer.Option(help="Team name or unique partial team name to inspect."),
    ],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Inspect one generated team feature vector."""
    inspection = inspect_team_vector(ProjectPaths.from_root(root), team=team)
    for line in format_feature_inspection(inspection):
        typer.echo(line)


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


@normalize_app.command("statsbomb-season")
def normalize_statsbomb_season(
    competition_id: Annotated[int, typer.Option(help="StatsBomb competition id.")],
    season_id: Annotated[int, typer.Option(help="StatsBomb season id.")],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(help="Maximum number of matches to normalize."),
    ] = None,
) -> None:
    """Normalize cached matches for one StatsBomb competition-season."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    normalized = normalize_season(
        client,
        competition_id=competition_id,
        season_id=season_id,
        limit=limit,
    )

    typer.echo("Normalized StatsBomb season")
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


@query_app.command("passes")
def query_passes(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int | None,
        typer.Option(help="Only show passes from this StatsBomb match id."),
    ] = None,
    team: Annotated[
        str | None,
        typer.Option(help="Only show passes by teams matching this text."),
    ] = None,
    player: Annotated[
        str | None,
        typer.Option(help="Only show passes by players matching this text."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of pass rows to show."),
    ] = 10,
) -> None:
    """Show passes from normalized StatsBomb tables."""
    paths = ProjectPaths.from_root(root)
    passes = load_passes(paths, match_id=match_id, team=team, player=player, limit=limit)

    typer.echo("Passes")
    for line in format_passes(passes):
        typer.echo(line)


@list_app.command("statsbomb-competitions")
def list_statsbomb_competitions(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of competition-season rows to show."),
    ] = 25,
) -> None:
    """List available StatsBomb competition-season IDs."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    options = list_competitions(client)

    typer.echo("StatsBomb competitions")
    for option in options[:limit]:
        typer.echo(format_competition_option(option))


@list_app.command("statsbomb-matches")
def list_statsbomb_matches(
    competition_id: Annotated[int, typer.Option(help="StatsBomb competition id.")],
    season_id: Annotated[int, typer.Option(help="StatsBomb season id.")],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of matches to show."),
    ] = 25,
) -> None:
    """List available StatsBomb matches for one competition-season."""
    paths = ProjectPaths.from_root(root)
    client = StatsBombOpenDataClient(paths)
    options = list_matches(client, competition_id=competition_id, season_id=season_id)

    typer.echo("StatsBomb matches")
    for option in options[:limit]:
        typer.echo(format_match_option(option))


@features_app.command("player-passing")
def features_player_passing(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int | None,
        typer.Option(help="Only build features from this StatsBomb match id."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of player rows to print."),
    ] = 10,
) -> None:
    """Build player passing features from normalized StatsBomb tables."""
    paths = ProjectPaths.from_root(root)
    features = build_player_passing_features(paths, match_id=match_id)

    typer.echo("Player passing features")
    for line in format_player_passing_features(features, limit=limit):
        typer.echo(line)


@features_app.command("player-carrying")
def features_player_carrying(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int | None,
        typer.Option(help="Only build features from this StatsBomb match id."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of player rows to print."),
    ] = 10,
) -> None:
    """Build player carrying features from normalized StatsBomb tables."""
    paths = ProjectPaths.from_root(root)
    features = build_player_carrying_features(paths, match_id=match_id)

    typer.echo("Player carrying features")
    for line in format_player_carrying_features(features, limit=limit):
        typer.echo(line)


@features_app.command("player-shooting")
def features_player_shooting(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int | None,
        typer.Option(help="Only build features from this StatsBomb match id."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of player rows to print."),
    ] = 10,
) -> None:
    """Build player shooting features from normalized StatsBomb tables."""
    paths = ProjectPaths.from_root(root)
    features = build_player_shooting_features(paths, match_id=match_id)

    typer.echo("Player shooting features")
    for line in format_player_shooting_features(features, limit=limit):
        typer.echo(line)


@features_app.command("player-matrix")
def features_player_matrix(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int | None,
        typer.Option(help="Only build features from this StatsBomb match id."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of player rows to print."),
    ] = 10,
) -> None:
    """Build a combined player feature matrix."""
    paths = ProjectPaths.from_root(root)
    matrix = build_player_feature_matrix(paths, match_id=match_id)

    typer.echo("Player feature matrix")
    for line in format_player_feature_matrix(matrix, limit=limit):
        typer.echo(line)


@features_app.command("team-matrix")
def features_team_matrix(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    match_id: Annotated[
        int | None,
        typer.Option(help="Only build features from this StatsBomb match id."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of team rows to print."),
    ] = 10,
) -> None:
    """Build a combined team feature matrix."""
    paths = ProjectPaths.from_root(root)
    matrix = build_team_feature_matrix(paths, match_id=match_id)

    typer.echo("Team feature matrix")
    for line in format_team_feature_matrix(matrix, limit=limit):
        typer.echo(line)


@similarity_app.command("players")
def similarity_players(
    player: Annotated[
        str,
        typer.Option(help="Player name or partial player name to compare from."),
    ],
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(help="Number of similar players to print."),
    ] = 5,
    same_position: Annotated[
        bool,
        typer.Option(help="Only compare players in the same broad position group."),
    ] = False,
    explain: Annotated[
        bool,
        typer.Option(help="Show shared traits and key differences for each result."),
    ] = False,
) -> None:
    """Find players with similar feature profiles."""
    paths = ProjectPaths.from_root(root)
    players = find_similar_players(
        paths,
        player=player,
        limit=limit,
        same_position=same_position,
    )

    typer.echo(f"Similar players to {player}")
    if explain:
        explanations = explain_similar_players(paths, player=player, players=players)
        lines = format_similar_players_with_explanations(
            players,
            limit=limit,
            explanations=explanations,
        )
    else:
        lines = format_similar_players(players, limit=limit)

    for line in lines:
        typer.echo(line)
