from pathlib import Path

import pandas as pd

from scoutgraph.features import player_matrix
from scoutgraph.features.player_matrix import build_player_feature_matrix, format_player_feature_matrix
from scoutgraph.storage.paths import ProjectPaths


def test_build_player_feature_matrix_joins_feature_groups_and_fills_missing_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_passing(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {
                    "player_id": 100,
                    "player_name": "Granit Xhaka",
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "passes_attempted": 85,
                    "passes_completed": 78,
                    "pass_completion_pct": 91.8,
                    "progressive_passes": 18,
                    "avg_pass_length": 17.2,
                }
            ]
        )

    def fake_carrying(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {
                    "player_id": 100,
                    "player_name": "Granit Xhaka",
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "carries": 76,
                    "progressive_carries": 4,
                    "avg_carry_distance": 4.81,
                    "carries_into_final_third": 2,
                    "carries_into_box": 0,
                },
                {
                    "player_id": 200,
                    "player_name": "Florian Wirtz",
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "carries": 20,
                    "progressive_carries": 8,
                    "avg_carry_distance": 7.5,
                    "carries_into_final_third": 5,
                    "carries_into_box": 1,
                },
            ]
        )

    def fake_shooting(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {
                    "player_id": 200,
                    "player_name": "Florian Wirtz",
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "shots": 5,
                    "goals": 3,
                    "xg": 0.871,
                    "avg_shot_distance": 20.75,
                    "shots_on_target": 3,
                    "shots_in_box": 3,
                }
            ]
        )

    def fake_minutes(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {"player_id": 100, "team_id": 10, "minutes_played": 90.0},
                {"player_id": 200, "team_id": 10, "minutes_played": 45.0},
            ]
        )

    monkeypatch.setattr(player_matrix, "build_player_passing_features", fake_passing)
    monkeypatch.setattr(player_matrix, "build_player_carrying_features", fake_carrying)
    monkeypatch.setattr(player_matrix, "build_player_shooting_features", fake_shooting)
    monkeypatch.setattr(player_matrix, "build_player_minutes", fake_minutes)

    matrix = build_player_feature_matrix(ProjectPaths.from_root(tmp_path), match_id=3895302)

    assert len(matrix) == 2
    xhaka = matrix[matrix["player_name"] == "Granit Xhaka"].iloc[0]
    wirtz = matrix[matrix["player_name"] == "Florian Wirtz"].iloc[0]
    assert xhaka["passes_attempted"] == 85
    assert xhaka["passes_attempted_per_90"] == 85
    assert xhaka["shots"] == 0
    assert wirtz["passes_attempted"] == 0
    assert wirtz["shots"] == 5
    assert wirtz["shots_per_90"] == 10
    assert (tmp_path / "data" / "processed" / "statsbomb" / "player_features.parquet").exists()


def test_format_player_feature_matrix_returns_readable_lines() -> None:
    lines = format_player_feature_matrix(
        pd.DataFrame(
            [
                {
                    "player_name": "Granit Xhaka",
                    "team_name": "Bayer Leverkusen",
                    "minutes_played": 90.0,
                    "passes_attempted": 85,
                    "carries": 76,
                    "shots": 3,
                    "xg": 0.103,
                },
                {
                    "player_name": "Florian Wirtz",
                    "team_name": "Bayer Leverkusen",
                    "minutes_played": 45.0,
                    "passes_attempted": 40,
                    "carries": 50,
                    "shots": 1,
                    "xg": 0.421,
                }
            ]
        )
    )

    assert lines == [
        "Granit Xhaka | Bayer Leverkusen | 90.0 minutes | "
        "85 passes | 76 carries | 3 shots | 0.103 xG",
        "Florian Wirtz | Bayer Leverkusen | 45.0 minutes | "
        "40 passes | 50 carries | 1 shot | 0.421 xG",
    ]
