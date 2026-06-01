import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PLAYER_POSITIONS_PATH = "statsbomb/player_positions.parquet"
POSITION_GROUPS = {
    "goalkeeper": {1},
    "defender": {2, 3, 4, 5, 6, 7, 8},
    "midfielder": {9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20},
    "forward": {17, 21, 22, 23, 24, 25},
}


def load_player_position_groups(paths: ProjectPaths) -> pd.DataFrame:
    """Load one broad position group for each player and team."""
    positions_path = paths.processed_data / PLAYER_POSITIONS_PATH
    if not positions_path.exists():
        msg = (
            "Player positions not found. "
            "Run a `scoutgraph normalize statsbomb-*` command before position-aware similarity."
        )
        raise FileNotFoundError(msg)

    positions = pd.read_parquet(positions_path)
    positions["position_group"] = positions["position_id"].map(position_group)

    counts = (
        positions.groupby(["player_id", "team_id", "position_group"], as_index=False)
        .size()
        .sort_values(
            ["player_id", "team_id", "size", "position_group"],
            ascending=[True, True, False, True],
        )
    )
    return counts.drop_duplicates(["player_id", "team_id"])[
        ["player_id", "team_id", "position_group"]
    ].reset_index(drop=True)


def position_group(position_id: int) -> str:
    """Collapse one detailed StatsBomb position into a broad comparison group."""
    for group, position_ids in POSITION_GROUPS.items():
        if position_id in position_ids:
            return group
    msg = f"Unsupported StatsBomb position id: {position_id}"
    raise ValueError(msg)
