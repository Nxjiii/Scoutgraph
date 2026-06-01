import pandas as pd

from scoutgraph.features.player_carrying import build_player_carrying_features
from scoutgraph.features.player_passing import build_player_passing_features
from scoutgraph.features.player_shooting import build_player_shooting_features
from scoutgraph.storage.paths import ProjectPaths


TEAM_ID_COLUMNS = ["team_id", "team_name"]


def build_team_feature_matrix(
    paths: ProjectPaths,
    *,
    match_id: int | None = None,
) -> pd.DataFrame:
    """Build a combined team feature matrix from current player feature groups."""
    passing = _build_team_passing_features(
        build_player_passing_features(paths, match_id=match_id)
    )
    carrying = _build_team_carrying_features(
        build_player_carrying_features(paths, match_id=match_id)
    )
    shooting = _build_team_shooting_features(
        build_player_shooting_features(paths, match_id=match_id)
    )

    matrix = passing.merge(carrying, on=TEAM_ID_COLUMNS, how="outer")
    matrix = matrix.merge(shooting, on=TEAM_ID_COLUMNS, how="outer")
    metric_columns = [column for column in matrix.columns if column not in TEAM_ID_COLUMNS]
    matrix[metric_columns] = matrix[metric_columns].fillna(0)
    matrix = matrix.sort_values(["passes_attempted", "team_name"], ascending=[False, True])

    output_path = paths.processed_data / "statsbomb" / "team_features.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_parquet(output_path, index=False)

    return matrix.reset_index(drop=True)


def format_team_feature_matrix(matrix: pd.DataFrame, *, limit: int = 10) -> list[str]:
    lines = []
    for _, row in matrix.head(limit).iterrows():
        lines.append(
            f"{row['team_name']} | "
            f"{int(row['passes_attempted'])} passes | "
            f"{row['pass_completion_pct']}% completed | "
            f"{int(row['progressive_passes'])} progressive passes | "
            f"{int(row['carries'])} carries | "
            f"{int(row['shots'])} shots | "
            f"{row['xg']} xG"
        )
    return lines


def _build_team_passing_features(features: pd.DataFrame) -> pd.DataFrame:
    teams = (
        features.groupby(TEAM_ID_COLUMNS, as_index=False)
        .agg(
            passes_attempted=("passes_attempted", "sum"),
            passes_completed=("passes_completed", "sum"),
            progressive_passes=("progressive_passes", "sum"),
        )
    )
    teams["pass_completion_pct"] = (
        teams["passes_completed"] / teams["passes_attempted"] * 100
    ).round(1)
    teams["avg_pass_length"] = _weighted_average(
        features,
        value_column="avg_pass_length",
        weight_column="passes_attempted",
    )
    return teams


def _build_team_carrying_features(features: pd.DataFrame) -> pd.DataFrame:
    teams = (
        features.groupby(TEAM_ID_COLUMNS, as_index=False)
        .agg(
            carries=("carries", "sum"),
            progressive_carries=("progressive_carries", "sum"),
            carries_into_final_third=("carries_into_final_third", "sum"),
            carries_into_box=("carries_into_box", "sum"),
        )
    )
    teams["avg_carry_distance"] = _weighted_average(
        features,
        value_column="avg_carry_distance",
        weight_column="carries",
    )
    return teams


def _build_team_shooting_features(features: pd.DataFrame) -> pd.DataFrame:
    teams = (
        features.groupby(TEAM_ID_COLUMNS, as_index=False)
        .agg(
            shots=("shots", "sum"),
            goals=("goals", "sum"),
            xg=("xg", "sum"),
            shots_on_target=("shots_on_target", "sum"),
            shots_in_box=("shots_in_box", "sum"),
        )
    )
    teams["xg"] = teams["xg"].round(3)
    teams["avg_shot_distance"] = _weighted_average(
        features,
        value_column="avg_shot_distance",
        weight_column="shots",
    )
    return teams


def _weighted_average(
    features: pd.DataFrame,
    *,
    value_column: str,
    weight_column: str,
) -> pd.Series:
    weighted_values = features[value_column] * features[weight_column]
    weighted_sums = weighted_values.groupby([features["team_id"], features["team_name"]]).sum()
    weight_sums = features.groupby(TEAM_ID_COLUMNS)[weight_column].sum()
    return (weighted_sums / weight_sums).round(2).reset_index(drop=True)
