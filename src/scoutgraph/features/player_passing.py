from pathlib import Path

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PLAYER_PASSING_COLUMNS = [
    "player_id",
    "player_name",
    "team_id",
    "team_name",
    "passes_attempted",
    "passes_completed",
    "pass_completion_pct",
    "progressive_passes",
    "avg_pass_length",
]


def build_player_passing_features(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
) -> pd.DataFrame:
    """Build player-level passing features from normalized StatsBomb tables."""
    processed_root = paths.processed_data / "statsbomb"
    events = _read_parquet(processed_root / "events.parquet")
    pass_events = _read_parquet(processed_root / "pass_events.parquet")

    if match_id is not None:
        events = events[events["match_id"] == match_id]

    passes = events.merge(pass_events, on="event_id", how="inner")
    passes = passes[passes["player_id"].notna()].copy()
    passes["is_completed"] = passes["outcome_name"] == "Complete"
    passes["is_progressive"] = _is_progressive_pass(passes)

    features = (
        passes.groupby(["player_id", "player_name", "team_id", "team_name"], dropna=False)
        .agg(
            passes_attempted=("event_id", "count"),
            passes_completed=("is_completed", "sum"),
            progressive_passes=("is_progressive", "sum"),
            avg_pass_length=("length", "mean"),
        )
        .reset_index()
    )
    features["pass_completion_pct"] = (
        features["passes_completed"] / features["passes_attempted"] * 100
    ).round(1)
    features["avg_pass_length"] = features["avg_pass_length"].round(2)

    features = features.loc[:, PLAYER_PASSING_COLUMNS].sort_values(
        ["passes_attempted", "player_name"],
        ascending=[False, True],
    )

    output_path = processed_root / "player_passing_features.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)

    return features.reset_index(drop=True)


def format_player_passing_features(features: pd.DataFrame, *, limit: int = 10) -> list[str]:
    lines = []
    for _, row in features.head(limit).iterrows():
        lines.append(
            f"{row['player_name']} | {row['team_name']} | "
            f"{row['passes_attempted']} attempted | "
            f"{row['passes_completed']} completed | "
            f"{row['pass_completion_pct']}% | "
            f"{row['progressive_passes']} progressive"
        )
    return lines


def _is_progressive_pass(passes: pd.DataFrame) -> pd.Series:
    return (
        passes["location_x"].notna()
        & passes["end_location_x"].notna()
        & ((passes["end_location_x"] - passes["location_x"]) >= 10)
    )


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing normalized table: {path}. Run a StatsBomb normalize command first."
        )
    return pd.read_parquet(path)

