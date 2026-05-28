from pathlib import Path

import pandas as pd

from scoutgraph.features.player_carrying import (
    build_player_carrying_features,
    format_player_carrying_features,
)
from scoutgraph.storage.paths import ProjectPaths


def test_build_player_carrying_features_aggregates_carry_metrics(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "event_id": "carry-1",
                "match_id": 1,
                "player_id": 100,
                "player_name": "Florian Wirtz",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "location_x": 70.0,
                "location_y": 40.0,
            },
            {
                "event_id": "carry-2",
                "match_id": 1,
                "player_id": 100,
                "player_name": "Florian Wirtz",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "location_x": 78.0,
                "location_y": 40.0,
            },
            {
                "event_id": "carry-3",
                "match_id": 2,
                "player_id": 200,
                "player_name": "Marvin Ducksch",
                "team_id": 20,
                "team_name": "Werder Bremen",
                "location_x": 50.0,
                "location_y": 40.0,
            },
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "carry-1",
                "end_location_x": 82.0,
                "end_location_y": 42.0,
                "carry_distance": 12.17,
            },
            {
                "event_id": "carry-2",
                "end_location_x": 103.0,
                "end_location_y": 40.0,
                "carry_distance": 25.0,
            },
            {
                "event_id": "carry-3",
                "end_location_x": 61.0,
                "end_location_y": 45.0,
                "carry_distance": 12.08,
            },
        ]
    ).to_parquet(processed_root / "carry_events.parquet", index=False)

    features = build_player_carrying_features(ProjectPaths.from_root(tmp_path), match_id=1)

    assert len(features) == 1
    assert features.loc[0, "player_name"] == "Florian Wirtz"
    assert features.loc[0, "carries"] == 2
    assert features.loc[0, "progressive_carries"] == 2
    assert features.loc[0, "avg_carry_distance"] == 18.58
    assert features.loc[0, "carries_into_final_third"] == 2
    assert features.loc[0, "carries_into_box"] == 1
    assert (processed_root / "player_carrying_features.parquet").exists()


def test_format_player_carrying_features_returns_readable_lines() -> None:
    lines = format_player_carrying_features(
        pd.DataFrame(
            [
                {
                    "player_name": "Florian Wirtz",
                    "team_name": "Bayer Leverkusen",
                    "carries": 42,
                    "progressive_carries": 12,
                    "avg_carry_distance": 8.4,
                    "carries_into_final_third": 6,
                    "carries_into_box": 2,
                }
            ]
        )
    )

    assert lines == [
        "Florian Wirtz | Bayer Leverkusen | "
        "42 carries | 12 progressive | 8.4 avg distance | "
        "6 into final third | 2 into box"
    ]
