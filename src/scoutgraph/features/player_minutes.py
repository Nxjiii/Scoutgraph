from pathlib import Path

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PLAYER_MINUTES_COLUMNS = ["player_id", "team_id", "minutes_played"]


def build_player_minutes(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
) -> pd.DataFrame:
    """Calculate player minutes from normalized StatsBomb position spells."""
    processed_root = paths.processed_data / "statsbomb"
    positions = _read_parquet(processed_root / "player_positions.parquet")
    events = _read_parquet(processed_root / "events.parquet")

    if match_id is not None:
        positions = positions[positions["match_id"] == match_id]
        events = events[events["match_id"] == match_id]

    match_end_seconds = (
        (events["minute"] * 60 + events["second"]).groupby(events["match_id"]).max().to_dict()
    )
    positions = positions.copy()
    positions["start_seconds"] = positions["from_time"].map(_timestamp_seconds)
    positions["end_seconds"] = positions.apply(
        lambda row: _position_end_seconds(row, match_end_seconds),
        axis=1,
    )

    minutes = (
        positions.groupby(["match_id", "player_id", "team_id"], as_index=False)
        .apply(_merged_interval_seconds, include_groups=False)
        .rename(columns={None: "seconds_played"})
    )
    minutes["minutes_played"] = (minutes["seconds_played"] / 60).round(2)

    return (
        minutes.groupby(["player_id", "team_id"], as_index=False)["minutes_played"]
        .sum()
        .loc[:, PLAYER_MINUTES_COLUMNS]
    )


def _merged_interval_seconds(positions: pd.DataFrame) -> int:
    intervals = sorted(zip(positions["start_seconds"], positions["end_seconds"], strict=True))
    merged: list[list[int]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def _position_end_seconds(row: pd.Series, match_end_seconds: dict[int, int]) -> int:
    if pd.notna(row["to_time"]):
        return _timestamp_seconds(row["to_time"])
    return match_end_seconds[row["match_id"]]


def _timestamp_seconds(timestamp: str) -> int:
    minutes, seconds = timestamp.split(":")
    return int(minutes) * 60 + int(seconds)


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing normalized table: {path}. Run a StatsBomb normalize command first."
        )
    return pd.read_parquet(path)
