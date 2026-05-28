from pathlib import Path

import pandas as pd

from scoutgraph.features.player_passing import (
    build_player_passing_features,
    format_player_passing_features,
)
from scoutgraph.storage.paths import ProjectPaths


def test_build_player_passing_features_aggregates_pass_metrics(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "match_id": 1,
                "player_id": 100,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "location_x": 40.0,
            },
            {
                "event_id": "pass-2",
                "match_id": 1,
                "player_id": 100,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "location_x": 50.0,
            },
            {
                "event_id": "pass-3",
                "match_id": 2,
                "player_id": 200,
                "player_name": "Marvin Ducksch",
                "team_id": 20,
                "team_name": "Werder Bremen",
                "location_x": 60.0,
            },
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "outcome_name": "Complete",
                "length": 12.0,
                "end_location_x": 55.0,
            },
            {
                "event_id": "pass-2",
                "outcome_name": "Incomplete",
                "length": 18.0,
                "end_location_x": 54.0,
            },
            {
                "event_id": "pass-3",
                "outcome_name": "Complete",
                "length": 20.0,
                "end_location_x": 75.0,
            },
        ]
    ).to_parquet(processed_root / "pass_events.parquet", index=False)

    features = build_player_passing_features(ProjectPaths.from_root(tmp_path), match_id=1)

    assert len(features) == 1
    assert features.loc[0, "player_name"] == "Granit Xhaka"
    assert features.loc[0, "passes_attempted"] == 2
    assert features.loc[0, "passes_completed"] == 1
    assert features.loc[0, "pass_completion_pct"] == 50.0
    assert features.loc[0, "progressive_passes"] == 1
    assert features.loc[0, "avg_pass_length"] == 15.0
    assert (processed_root / "player_passing_features.parquet").exists()


def test_format_player_passing_features_returns_readable_lines() -> None:
    lines = format_player_passing_features(
        pd.DataFrame(
            [
                {
                    "player_name": "Granit Xhaka",
                    "team_name": "Bayer Leverkusen",
                    "passes_attempted": 92,
                    "passes_completed": 88,
                    "pass_completion_pct": 95.7,
                    "progressive_passes": 14,
                }
            ]
        )
    )

    assert lines == [
        "Granit Xhaka | Bayer Leverkusen | "
        "92 attempted | 88 completed | 95.7% | 14 progressive"
    ]

