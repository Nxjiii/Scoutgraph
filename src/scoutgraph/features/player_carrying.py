from pathlib import Path

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PLAYER_CARRYING_COLUMNS = [
    "player_id",
    "player_name",
    "team_id",
    "team_name",
    "carries",
    "progressive_carries",
    "avg_carry_distance",
    "carries_into_final_third",
    "carries_into_box",
]


def build_player_carrying_features(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
) -> pd.DataFrame:
    """Build player-level carrying features from normalized StatsBomb tables."""
    processed_root = paths.processed_data / "statsbomb"
    events = _read_parquet(processed_root / "events.parquet")
    carry_events = _read_parquet(processed_root / "carry_events.parquet")

    if match_id is not None:
        events = events[events["match_id"] == match_id]

    carries = events.merge(carry_events, on="event_id", how="inner")
    carries = carries[carries["player_id"].notna()].copy()
    carries["is_progressive"] = _is_progressive_carry(carries)
    carries["is_into_final_third"] = (carries["location_x"] < 80) & (
        carries["end_location_x"] >= 80
    )
    carries["is_into_box"] = (
        (carries["end_location_x"] >= 102)
        & (carries["end_location_y"] >= 18)
        & (carries["end_location_y"] <= 62)
    )

    features = (
        carries.groupby(["player_id", "player_name", "team_id", "team_name"], dropna=False)
        .agg(
            carries=("event_id", "count"),
            progressive_carries=("is_progressive", "sum"),
            avg_carry_distance=("carry_distance", "mean"),
            carries_into_final_third=("is_into_final_third", "sum"),
            carries_into_box=("is_into_box", "sum"),
        )
        .reset_index()
    )
    features["avg_carry_distance"] = features["avg_carry_distance"].round(2)

    features = features.loc[:, PLAYER_CARRYING_COLUMNS].sort_values(
        ["carries", "player_name"],
        ascending=[False, True],
    )

    output_path = processed_root / "player_carrying_features.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)

    return features.reset_index(drop=True)


def format_player_carrying_features(features: pd.DataFrame, *, limit: int = 10) -> list[str]:
    lines = []
    for _, row in features.head(limit).iterrows():
        lines.append(
            f"{row['player_name']} | {row['team_name']} | "
            f"{row['carries']} carries | "
            f"{row['progressive_carries']} progressive | "
            f"{row['avg_carry_distance']} avg distance | "
            f"{row['carries_into_final_third']} into final third | "
            f"{row['carries_into_box']} into box"
        )
    return lines


def _is_progressive_carry(carries: pd.DataFrame) -> pd.Series:
    return (
        carries["location_x"].notna()
        & carries["end_location_x"].notna()
        & ((carries["end_location_x"] - carries["location_x"]) >= 10)
    )


def _read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing normalized table: {path}. Run a StatsBomb normalize command first."
        )
    return pd.read_parquet(path)

