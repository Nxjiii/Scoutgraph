from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.query.sample import format_pass_row, load_passes, load_sample_passes
from scoutgraph.storage.paths import ProjectPaths


def test_load_sample_passes_joins_events_to_pass_events_in_event_order(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "event_id": "pass-2",
                "match_id": 2,
                "event_index": 2,
                "timestamp": "00:00:05.000",
                "team_name": "Bayer Leverkusen",
                "player_name": "Granit Xhaka",
                "location_x": 50.0,
                "location_y": 30.0,
            },
            {
                "event_id": "pass-1",
                "match_id": 1,
                "event_index": 1,
                "timestamp": "00:00:03.000",
                "team_name": "Werder Bremen",
                "player_name": "Nick Woltemade",
                "location_x": 61.0,
                "location_y": 40.1,
            },
            {
                "event_id": "carry-1",
                "match_id": 1,
                "event_index": 3,
                "timestamp": "00:00:06.000",
                "team_name": "Bayer Leverkusen",
                "player_name": "Granit Xhaka",
                "location_x": 51.0,
                "location_y": 30.0,
            },
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "recipient_player_name": "Marvin Ducksch",
                "end_location_x": 59.0,
                "end_location_y": 40.9,
                "outcome_name": "Complete",
            },
            {
                "event_id": "pass-2",
                "recipient_player_name": "Florian Wirtz",
                "end_location_x": 75.0,
                "end_location_y": 31.0,
                "outcome_name": "Complete",
            },
        ]
    ).to_parquet(processed_root / "pass_events.parquet", index=False)

    passes = load_sample_passes(ProjectPaths.from_root(tmp_path), limit=1)

    assert len(passes) == 1
    assert passes.loc[0, "event_id"] == "pass-1"
    assert passes.loc[0, "recipient_player_name"] == "Marvin Ducksch"


def test_load_passes_can_filter_by_match_id(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "match_id": 1,
                "event_index": 1,
                "timestamp": "00:00:01.000",
                "team_name": "Team A",
                "player_name": "Player One",
                "location_x": 10.0,
                "location_y": 20.0,
            },
            {
                "event_id": "pass-2",
                "match_id": 2,
                "event_index": 2,
                "timestamp": "00:00:02.000",
                "team_name": "Team B",
                "player_name": "Player Two",
                "location_x": 30.0,
                "location_y": 40.0,
            },
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "recipient_player_name": "Player Three",
                "end_location_x": 11.0,
                "end_location_y": 21.0,
                "outcome_name": "Complete",
            },
            {
                "event_id": "pass-2",
                "recipient_player_name": "Player Four",
                "end_location_x": 31.0,
                "end_location_y": 41.0,
                "outcome_name": "Incomplete",
            },
        ]
    ).to_parquet(processed_root / "pass_events.parquet", index=False)

    passes = load_passes(ProjectPaths.from_root(tmp_path), match_id=2)

    assert len(passes) == 1
    assert passes.loc[0, "event_id"] == "pass-2"
    assert passes.loc[0, "team_name"] == "Team B"


def test_load_passes_can_filter_by_team_and_player_case_insensitively(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "match_id": 1,
                "event_index": 1,
                "timestamp": "00:00:01.000",
                "team_name": "Bayer Leverkusen",
                "player_name": "Granit Xhaka",
                "location_x": 10.0,
                "location_y": 20.0,
            },
            {
                "event_id": "pass-2",
                "match_id": 1,
                "event_index": 2,
                "timestamp": "00:00:02.000",
                "team_name": "Werder Bremen",
                "player_name": "Marvin Ducksch",
                "location_x": 30.0,
                "location_y": 40.0,
            },
        ]
    ).to_parquet(processed_root / "events.parquet", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "pass-1",
                "recipient_player_name": "Florian Wirtz",
                "end_location_x": 11.0,
                "end_location_y": 21.0,
                "outcome_name": "Complete",
            },
            {
                "event_id": "pass-2",
                "recipient_player_name": "Romano Schmid",
                "end_location_x": 31.0,
                "end_location_y": 41.0,
                "outcome_name": "Complete",
            },
        ]
    ).to_parquet(processed_root / "pass_events.parquet", index=False)

    passes = load_passes(ProjectPaths.from_root(tmp_path), team="leverkusen", player="xhaka")

    assert len(passes) == 1
    assert passes.loc[0, "team_name"] == "Bayer Leverkusen"
    assert passes.loc[0, "player_name"] == "Granit Xhaka"


def test_format_pass_row_returns_readable_terminal_line() -> None:
    line = format_pass_row(
        pd.Series(
            {
                "timestamp": "00:00:03.417",
                "team_name": "Werder Bremen",
                "player_name": "Nick Woltemade",
                "location_x": 61.0,
                "location_y": 40.1,
                "recipient_player_name": "Marvin Ducksch",
                "end_location_x": 59.0,
                "end_location_y": 40.9,
                "outcome_name": "Complete",
            }
        )
    )

    assert (
        line
        == "00:00:03.417 | Werder Bremen | Nick Woltemade | "
        "[61.0, 40.1] -> Marvin Ducksch -> [59.0, 40.9] | Complete"
    )


def test_load_sample_passes_raises_when_normalized_tables_are_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Run `scoutgraph normalize statsbomb-sample` first"):
        load_sample_passes(ProjectPaths.from_root(tmp_path))
