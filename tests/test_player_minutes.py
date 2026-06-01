from pathlib import Path

import pandas as pd

from scoutgraph.features.player_minutes import build_player_minutes
from scoutgraph.storage.paths import ProjectPaths


def test_build_player_minutes_merges_position_spells_and_uses_match_end(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "match_id": 1,
                "player_id": 100,
                "team_id": 10,
                "from_time": "00:00",
                "to_time": "45:00",
            },
            {
                "match_id": 1,
                "player_id": 100,
                "team_id": 10,
                "from_time": "45:00",
                "to_time": None,
            },
            {
                "match_id": 1,
                "player_id": 200,
                "team_id": 10,
                "from_time": "60:00",
                "to_time": None,
            },
        ]
    ).to_parquet(processed_root / "player_positions.parquet", index=False)
    pd.DataFrame(
        [
            {"match_id": 1, "minute": 0, "second": 0},
            {"match_id": 1, "minute": 90, "second": 0},
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)

    minutes = build_player_minutes(ProjectPaths.from_root(tmp_path))

    assert minutes.to_dict("records") == [
        {"player_id": 100, "team_id": 10, "minutes_played": 90.0},
        {"player_id": 200, "team_id": 10, "minutes_played": 30.0},
    ]
