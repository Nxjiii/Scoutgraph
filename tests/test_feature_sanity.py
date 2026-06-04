from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.features.sanity import (
    format_feature_inspection,
    inspect_player_vector,
    inspect_team_vector,
)
from scoutgraph.storage.paths import ProjectPaths


def test_inspect_player_vector_flags_low_minutes_and_invalid_values(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Example Player",
                "team_id": 10,
                "team_name": "Example Team",
                "minutes_played": 20.0,
                "passes_attempted": 4,
                "passes_completed": 5,
                "pass_completion_pct": 125.0,
                "shots": 1,
                "goals": 2,
                "shots_on_target": 2,
                "passes_attempted_per_90": 18.0,
            }
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)

    inspection = inspect_player_vector(ProjectPaths.from_root(tmp_path), player="example")

    assert inspection.title == "Example Player | Example Team"
    assert "Low-minute sample: per-90 metrics may be unstable." in inspection.warnings
    assert "Completed passes exceed attempted passes." in inspection.warnings
    assert "Pass completion percentage is above 100." in inspection.warnings
    assert "Goals exceed shots." in inspection.warnings
    assert "Shots on target exceed total shots." in inspection.warnings


def test_inspect_team_vector_reports_clean_vector(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "team_id": 10,
                "team_name": "Example Team",
                "passes_attempted": 100,
                "passes_completed": 85,
                "pass_completion_pct": 85.0,
                "shots": 5,
                "goals": 1,
                "shots_on_target": 2,
            }
        ]
    ).to_parquet(processed_root / "team_features.parquet", index=False)

    inspection = inspect_team_vector(ProjectPaths.from_root(tmp_path), team="example")

    assert inspection.title == "Example Team"
    assert inspection.warnings == ()
    assert ("passes_attempted", 100.0) in inspection.metrics


def test_inspect_player_vector_rejects_ambiguous_name(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {"player_id": 1, "player_name": "Alex One", "team_id": 10, "team_name": "Team"},
            {"player_id": 2, "player_name": "Alex Two", "team_id": 10, "team_name": "Team"},
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)

    with pytest.raises(ValueError, match="Multiple matches found"):
        inspect_player_vector(ProjectPaths.from_root(tmp_path), player="Alex")


def test_format_feature_inspection_groups_metrics_and_warnings(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "team_id": 10,
                "team_name": "Example Team",
                "passes_attempted": 100,
                "passes_completed": 85,
                "pass_completion_pct": 85.0,
                "shots": 5,
                "goals": 1,
                "shots_on_target": 2,
            }
        ]
    ).to_parquet(processed_root / "team_features.parquet", index=False)

    lines = format_feature_inspection(
        inspect_team_vector(ProjectPaths.from_root(tmp_path), team="Example")
    )

    assert lines[:3] == ["Example Team", "", "Metrics"]
    assert "- passes attempted: 100.0" in lines
    assert lines[-2:] == ["Warnings", "- None"]
