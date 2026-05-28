from pathlib import Path

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PLAYER_SHOOTING_COLUMNS = [
    "player_id",
    "player_name",
    "team_id",
    "team_name",
    "shots",
    "goals",
    "xg",
    "avg_shot_distance",
    "shots_on_target",
    "shots_in_box",
]


def build_player_shooting_features(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
) -> pd.DataFrame:
    """Build player-level shooting features from normalized StatsBomb tables."""
    processed_root = paths.processed_data / "statsbomb"
    events = _read_parquet(processed_root / "events.parquet")
    shot_events = _read_parquet(processed_root / "shot_events.parquet")

    if match_id is not None:
        events = events[events["match_id"] == match_id]

    shots = events.merge(shot_events, on="event_id", how="inner")
    shots = shots[shots["player_id"].notna()].copy()
    shots["is_goal"] = shots["outcome_name"] == "Goal"
    shots["is_on_target"] = shots["outcome_name"].isin(["Goal", "Saved", "Saved to Post"])
    shots["is_in_box"] = (
        (shots["location_x"] >= 102) & (shots["location_y"] >= 18) & (shots["location_y"] <= 62)
    )

    features = (
        shots.groupby(["player_id", "player_name", "team_id", "team_name"], dropna=False)
        .agg(
            shots=("event_id", "count"),
            goals=("is_goal", "sum"),
            xg=("xg", "sum"),
            avg_shot_distance=("shot_distance", "mean"),
            shots_on_target=("is_on_target", "sum"),
            shots_in_box=("is_in_box", "sum"),
        )
        .reset_index()
    )
    features["xg"] = features["xg"].round(3)
    features["avg_shot_distance"] = features["avg_shot_distance"].round(2)

    features = features.loc[:, PLAYER_SHOOTING_COLUMNS].sort_values(
        ["shots", "xg", "player_name"],
        ascending=[False, False, True],
    )

    output_path = processed_root / "player_shooting_features.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)

    return features.reset_index(drop=True)


def format_player_shooting_features(features: pd.DataFrame, *, limit: int = 10) -> list[str]:
    lines = []
    for _, row in features.head(limit).iterrows():
        lines.append(
            f"{row['player_name']} | {row['team_name']} | "
            f"{row['shots']} shots | "
            f"{row['goals']} goals | "
            f"{row['xg']} xG | "
            f"{row['avg_shot_distance']} avg distance | "
            f"{row['shots_on_target']} on target | "
            f"{row['shots_in_box']} in box"
        )
    return lines


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing normalized table: {path}. Run a StatsBomb normalize command first."
        )
    return pd.read_parquet(path)

