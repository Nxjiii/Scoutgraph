from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.similarity.player_positions import load_player_position_groups, position_group
from scoutgraph.storage.paths import ProjectPaths


def test_position_group_collapses_detailed_statsbomb_positions() -> None:
    assert position_group(1) == "goalkeeper"
    assert position_group(4) == "defender"
    assert position_group(9) == "midfielder"
    assert position_group(23) == "forward"


def test_position_group_raises_for_unsupported_position() -> None:
    with pytest.raises(ValueError, match="Unsupported StatsBomb position id"):
        position_group(99)


def test_load_player_position_groups_uses_most_common_group(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {"player_id": 1, "team_id": 10, "position_id": 9},
            {"player_id": 1, "team_id": 10, "position_id": 11},
            {"player_id": 1, "team_id": 10, "position_id": 4},
            {"player_id": 2, "team_id": 10, "position_id": 23},
        ]
    ).to_parquet(processed_root / "player_positions.parquet", index=False)

    positions = load_player_position_groups(ProjectPaths.from_root(tmp_path))

    assert positions.to_dict("records") == [
        {"player_id": 1, "team_id": 10, "position_group": "midfielder"},
        {"player_id": 2, "team_id": 10, "position_group": "forward"},
    ]
