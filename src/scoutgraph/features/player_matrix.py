import pandas as pd

from scoutgraph.features.player_carrying import build_player_carrying_features
from scoutgraph.features.player_minutes import build_player_minutes
from scoutgraph.features.player_passing import build_player_passing_features
from scoutgraph.features.player_shooting import build_player_shooting_features
from scoutgraph.storage.paths import ProjectPaths


PLAYER_ID_COLUMNS = ["player_id", "player_name", "team_id", "team_name"]
COUNT_METRIC_COLUMNS = [
    "passes_attempted",
    "passes_completed",
    "progressive_passes",
    "carries",
    "progressive_carries",
    "carries_into_final_third",
    "carries_into_box",
    "shots",
    "goals",
    "shots_on_target",
    "shots_in_box",
]
PER_90_METRIC_COLUMNS = [*COUNT_METRIC_COLUMNS, "xg"]


def build_player_feature_matrix(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
) -> pd.DataFrame:
    """Build a combined player feature matrix from all current feature groups."""
    passing = build_player_passing_features(paths, match_id=match_id)
    carrying = build_player_carrying_features(paths, match_id=match_id)
    shooting = build_player_shooting_features(paths, match_id=match_id)
    minutes = build_player_minutes(paths, match_id=match_id)

    matrix = _outer_join_feature_groups([passing, carrying, shooting])
    matrix = matrix.merge(minutes, on=["player_id", "team_id"], how="left")
    metric_columns = [column for column in matrix.columns if column not in PLAYER_ID_COLUMNS]
    matrix[metric_columns] = matrix[metric_columns].fillna(0)
    count_columns = [column for column in COUNT_METRIC_COLUMNS if column in matrix.columns]
    matrix[count_columns] = matrix[count_columns].astype(int)
    matrix = _add_per_90_metrics(matrix)

    matrix = matrix.sort_values(
        ["passes_attempted", "carries", "shots", "player_name"],
        ascending=[False, False, False, True],
    )

    output_path = paths.processed_data / "statsbomb" / "player_features.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_parquet(output_path, index=False)

    return matrix.reset_index(drop=True)


def _add_per_90_metrics(matrix: pd.DataFrame) -> pd.DataFrame:
    for column in PER_90_METRIC_COLUMNS:
        if column not in matrix.columns:
            continue
        matrix[f"{column}_per_90"] = (
            matrix[column]
            .div(matrix["minutes_played"].where(matrix["minutes_played"] > 0))
            .mul(90)
            .fillna(0)
            .round(3)
        )
    return matrix


def format_player_feature_matrix(matrix: pd.DataFrame, *, limit: int = 10) -> list[str]:
    lines = []
    for _, row in matrix.head(limit).iterrows():
        shots = int(row["shots"])
        lines.append(
            f"{row['player_name']} | {row['team_name']} | "
            f"{row['minutes_played']} minutes | "
            f"{int(row['passes_attempted'])} passes | "
            f"{int(row['carries'])} carries | "
            f"{shots} {_plural('shot', shots)} | "
            f"{row['xg']} xG"
        )
    return lines


def _outer_join_feature_groups(feature_groups: list[pd.DataFrame]) -> pd.DataFrame:
    matrix = feature_groups[0]
    for feature_group in feature_groups[1:]:
        matrix = matrix.merge(feature_group, on=PLAYER_ID_COLUMNS, how="outer")
    return matrix


def _plural(label: str, count: int) -> str:
    if count == 1:
        return label
    return f"{label}s"
