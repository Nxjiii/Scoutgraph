from pathlib import Path

import pandas as pd

from scoutgraph.features.player_shooting import (
    build_player_shooting_features,
    format_player_shooting_features,
)
from scoutgraph.storage.paths import ProjectPaths


def test_build_player_shooting_features_aggregates_shot_metrics(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "event_id": "shot-1",
                "match_id": 1,
                "player_id": 100,
                "player_name": "Victor Boniface",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "location_x": 108.0,
                "location_y": 40.0,
            },
            {
                "event_id": "shot-2",
                "match_id": 1,
                "player_id": 100,
                "player_name": "Victor Boniface",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "location_x": 95.0,
                "location_y": 40.0,
            },
            {
                "event_id": "shot-3",
                "match_id": 2,
                "player_id": 200,
                "player_name": "Marvin Ducksch",
                "team_id": 20,
                "team_name": "Werder Bremen",
                "location_x": 110.0,
                "location_y": 39.0,
            },
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "shot-1",
                "xg": 0.5,
                "outcome_name": "Goal",
                "shot_distance": 12.0,
            },
            {
                "event_id": "shot-2",
                "xg": 0.1,
                "outcome_name": "Off T",
                "shot_distance": 25.0,
            },
            {
                "event_id": "shot-3",
                "xg": 0.3,
                "outcome_name": "Saved",
                "shot_distance": 10.0,
            },
        ]
    ).to_parquet(processed_root / "shot_events.parquet", index=False)

    features = build_player_shooting_features(ProjectPaths.from_root(tmp_path), match_id=1)

    assert len(features) == 1
    assert features.loc[0, "player_name"] == "Victor Boniface"
    assert features.loc[0, "shots"] == 2
    assert features.loc[0, "goals"] == 1
    assert features.loc[0, "xg"] == 0.6
    assert features.loc[0, "avg_shot_distance"] == 18.5
    assert features.loc[0, "shots_on_target"] == 1
    assert features.loc[0, "shots_in_box"] == 1
    assert (processed_root / "player_shooting_features.parquet").exists()


def test_format_player_shooting_features_returns_readable_lines() -> None:
    lines = format_player_shooting_features(
        pd.DataFrame(
            [
                {
                    "player_name": "Victor Boniface",
                    "team_name": "Bayer Leverkusen",
                    "shots": 5,
                    "goals": 2,
                    "xg": 1.234,
                    "avg_shot_distance": 14.2,
                    "shots_on_target": 3,
                    "shots_in_box": 4,
                }
            ]
        )
    )

    assert lines == [
        "Victor Boniface | Bayer Leverkusen | "
        "5 shots | 2 goals | 1.234 xG | 14.2 avg distance | "
        "3 on target | 4 in box"
    ]

