from pathlib import Path

import pandas as pd

from scoutgraph.features import team_matrix
from scoutgraph.features.team_matrix import build_team_feature_matrix, format_team_feature_matrix
from scoutgraph.storage.paths import ProjectPaths


def test_build_team_feature_matrix_aggregates_player_features(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_passing(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "passes_attempted": 80,
                    "passes_completed": 72,
                    "progressive_passes": 12,
                    "avg_pass_length": 10.0,
                },
                {
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "passes_attempted": 20,
                    "passes_completed": 8,
                    "progressive_passes": 3,
                    "avg_pass_length": 20.0,
                },
            ]
        )

    def fake_carrying(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "carries": 30,
                    "progressive_carries": 4,
                    "avg_carry_distance": 4.0,
                    "carries_into_final_third": 2,
                    "carries_into_box": 1,
                },
                {
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "carries": 10,
                    "progressive_carries": 2,
                    "avg_carry_distance": 8.0,
                    "carries_into_final_third": 1,
                    "carries_into_box": 0,
                },
            ]
        )

    def fake_shooting(paths, *, match_id=None):
        return pd.DataFrame(
            [
                {
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "shots": 4,
                    "goals": 1,
                    "xg": 0.8,
                    "avg_shot_distance": 12.0,
                    "shots_on_target": 2,
                    "shots_in_box": 3,
                },
                {
                    "team_id": 10,
                    "team_name": "Bayer Leverkusen",
                    "shots": 1,
                    "goals": 0,
                    "xg": 0.1,
                    "avg_shot_distance": 22.0,
                    "shots_on_target": 0,
                    "shots_in_box": 0,
                },
            ]
        )

    monkeypatch.setattr(team_matrix, "build_player_passing_features", fake_passing)
    monkeypatch.setattr(team_matrix, "build_player_carrying_features", fake_carrying)
    monkeypatch.setattr(team_matrix, "build_player_shooting_features", fake_shooting)

    matrix = build_team_feature_matrix(ProjectPaths.from_root(tmp_path), match_id=3895302)

    assert len(matrix) == 1
    assert matrix.loc[0, "passes_attempted"] == 100
    assert matrix.loc[0, "pass_completion_pct"] == 80.0
    assert matrix.loc[0, "progressive_passes"] == 15
    assert matrix.loc[0, "avg_pass_length"] == 12.0
    assert matrix.loc[0, "carries"] == 40
    assert matrix.loc[0, "avg_carry_distance"] == 5.0
    assert matrix.loc[0, "shots"] == 5
    assert matrix.loc[0, "xg"] == 0.9
    assert matrix.loc[0, "avg_shot_distance"] == 14.0
    assert (tmp_path / "data" / "processed" / "statsbomb" / "team_features.parquet").exists()


def test_format_team_feature_matrix_returns_readable_lines() -> None:
    lines = format_team_feature_matrix(
        pd.DataFrame(
            [
                {
                    "team_name": "Bayer Leverkusen",
                    "passes_attempted": 722,
                    "pass_completion_pct": 89.2,
                    "progressive_passes": 53,
                    "carries": 621,
                    "shots": 17,
                    "xg": 1.987,
                }
            ]
        )
    )

    assert lines == [
        "Bayer Leverkusen | 722 passes | 89.2% completed | "
        "53 progressive passes | 621 carries | 17 shots | 1.987 xG"
    ]
