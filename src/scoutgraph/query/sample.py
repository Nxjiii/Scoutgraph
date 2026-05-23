from pathlib import Path

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PASS_QUERY_COLUMNS = [
    "event_id",
    "event_index",
    "timestamp",
    "team_name",
    "player_name",
    "location_x",
    "location_y",
    "recipient_player_name",
    "end_location_x",
    "end_location_y",
    "outcome_name",
]


def load_sample_passes(paths: ProjectPaths, limit: int = 10) -> pd.DataFrame:
    """Return readable pass rows from the normalized StatsBomb sample."""
    return load_passes(paths, limit=limit)


def load_passes(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
    team: str | None = None,
    player: str | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Return readable pass rows from normalized StatsBomb tables."""
    processed_root = paths.processed_data / "statsbomb"
    events = _read_parquet(processed_root / "events.parquet")
    pass_events = _read_parquet(processed_root / "pass_events.parquet")

    if match_id is not None:
        events = events[events["match_id"] == match_id]
    if team is not None:
        events = events[events["team_name"].str.contains(team, case=False, na=False)]
    if player is not None:
        events = events[events["player_name"].str.contains(player, case=False, na=False)]

    passes = (
        events.merge(pass_events, on="event_id", how="inner")
        .sort_values("event_index")
        .loc[:, PASS_QUERY_COLUMNS]
        .head(limit)
        .reset_index(drop=True)
    )

    return passes


def format_pass_row(row: pd.Series) -> str:
    """Format one pass row for terminal output."""
    start = _format_location(row["location_x"], row["location_y"])
    end = _format_location(row["end_location_x"], row["end_location_y"])
    return (
        f"{row['timestamp']} | {row['team_name']} | {row['player_name']} | "
        f"{start} -> {row['recipient_player_name']} -> {end} | {row['outcome_name']}"
    )


def format_passes(passes: pd.DataFrame) -> list[str]:
    return [format_pass_row(row) for _, row in passes.iterrows()]


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing normalized table: {path}. Run `scoutgraph normalize statsbomb-sample` first."
        )
    return pd.read_parquet(path)


def _format_location(x: float | None, y: float | None) -> str:
    if pd.isna(x) or pd.isna(y):
        return "[?, ?]"
    return f"[{x:.1f}, {y:.1f}]"
