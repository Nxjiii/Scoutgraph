from dataclasses import dataclass

import pandas as pd

from scoutgraph.similarity.player_positions import load_player_position_groups
from scoutgraph.similarity.player_similarity import load_player_feature_matrix
from scoutgraph.storage.paths import ProjectPaths


PROFILE_METRICS = (
    "minutes_played",
    "passes_attempted_per_90",
    "passes_completed_per_90",
    "progressive_passes_per_90",
    "pass_completion_pct",
    "avg_pass_length",
    "carries_per_90",
    "progressive_carries_per_90",
    "carries_into_final_third_per_90",
    "carries_into_box_per_90",
    "avg_carry_distance",
    "shots_per_90",
    "shots_on_target_per_90",
    "shots_in_box_per_90",
    "goals_per_90",
    "xg_per_90",
    "avg_shot_distance",
)


@dataclass(frozen=True)
class PlayerSummary:
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    position_group: str | None


@dataclass(frozen=True)
class PlayerProfile:
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    position_group: str | None
    metrics: dict[str, float]


def search_players(
    paths: ProjectPaths,
    *,
    query: str,
    limit: int = 10,
) -> list[PlayerSummary]:
    """Search generated player profiles by case-insensitive partial name."""
    matrix = _with_position_groups(paths, load_player_feature_matrix(paths))
    matches = matrix[matrix["player_name"].str.contains(query, case=False, na=False, regex=False)]
    matches = matches.sort_values(["player_name", "team_name"]).head(limit)
    return [_summary(row) for _, row in matches.iterrows()]


def get_player_profile(paths: ProjectPaths, *, player: str) -> PlayerProfile:
    """Return identifying information and public profile metrics for one player."""
    matrix = _with_position_groups(paths, load_player_feature_matrix(paths))
    row = _find_unique_player(matrix, player)
    metrics = {
        metric: float(row[metric])
        for metric in PROFILE_METRICS
        if metric in row.index and pd.notna(row[metric])
    }
    summary = _summary(row)
    return PlayerProfile(
        player_id=summary.player_id,
        player_name=summary.player_name,
        team_id=summary.team_id,
        team_name=summary.team_name,
        position_group=summary.position_group,
        metrics=metrics,
    )


def _with_position_groups(paths: ProjectPaths, matrix: pd.DataFrame) -> pd.DataFrame:
    if "position_group" in matrix.columns:
        return matrix
    positions = load_player_position_groups(paths)
    return matrix.merge(positions, on=["player_id", "team_id"], how="left")


def _find_unique_player(matrix: pd.DataFrame, player: str) -> pd.Series:
    exact = matrix[matrix["player_name"].str.casefold() == player.casefold()]
    matches = exact
    if exact.empty:
        matches = matrix[
            matrix["player_name"].str.contains(player, case=False, na=False, regex=False)
        ]
    if matches.empty:
        raise ValueError(f"No player found matching {player!r}.")
    if len(matches) > 1:
        names = ", ".join(matches["player_name"].astype(str).tolist())
        raise ValueError(f"Multiple matches found for {player!r}: {names}. Use a more specific name.")
    return matches.iloc[0]


def _summary(row: pd.Series) -> PlayerSummary:
    position = row.get("position_group")
    return PlayerSummary(
        player_id=int(row["player_id"]),
        player_name=str(row["player_name"]),
        team_id=int(row["team_id"]),
        team_name=str(row["team_name"]),
        position_group=None if pd.isna(position) else str(position),
    )
