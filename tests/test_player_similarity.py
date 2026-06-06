from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.similarity.player_similarity import (
    evaluate_similar_player_confidence,
    explain_similar_players,
    find_similar_players,
    format_similar_players,
    format_similar_players_with_explanations,
    load_player_feature_matrix,
)
from scoutgraph.storage.paths import ProjectPaths


def test_find_similar_players_returns_nearest_normalized_profiles(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 100,
                "progressive_passes_per_90": 20,
                "carries_per_90": 30,
                "shots_per_90": 1,
                "xg_per_90": 0.1,
            },
            {
                "player_id": 2,
                "player_name": "Robert Andrich",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 95,
                "progressive_passes_per_90": 18,
                "carries_per_90": 28,
                "shots_per_90": 1,
                "xg_per_90": 0.08,
            },
            {
                "player_id": 3,
                "player_name": "Victor Boniface",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 20,
                "progressive_passes_per_90": 2,
                "carries_per_90": 12,
                "shots_per_90": 6,
                "xg_per_90": 1.2,
            },
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)

    players = find_similar_players(ProjectPaths.from_root(tmp_path), player="xhaka", limit=2)

    assert players["player_name"].tolist() == ["Robert Andrich", "Victor Boniface"]
    assert players.loc[0, "similarity"] > players.loc[1, "similarity"]


def test_find_similar_players_raises_for_missing_player(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 100,
            }
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)

    with pytest.raises(ValueError, match="No player found"):
        find_similar_players(ProjectPaths.from_root(tmp_path), player="Saka")


def test_find_similar_players_can_filter_to_same_position_group(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 100,
                "progressive_passes_per_90": 20,
            },
            {
                "player_id": 2,
                "player_name": "Jonathan Tah",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 99,
                "progressive_passes_per_90": 19,
            },
            {
                "player_id": 3,
                "player_name": "Robert Andrich",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 80,
                "progressive_passes_per_90": 15,
            },
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)
    pd.DataFrame(
        [
            {"player_id": 1, "team_id": 10, "position_id": 9},
            {"player_id": 2, "team_id": 10, "position_id": 4},
            {"player_id": 3, "team_id": 10, "position_id": 11},
        ]
    ).to_parquet(processed_root / "player_positions.parquet", index=False)

    players = find_similar_players(
        ProjectPaths.from_root(tmp_path),
        player="Xhaka",
        same_position=True,
    )

    assert players["player_name"].tolist() == ["Robert Andrich"]


def test_load_player_feature_matrix_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Player feature matrix not found"):
        load_player_feature_matrix(ProjectPaths.from_root(tmp_path))


def test_format_similar_players_returns_readable_lines() -> None:
    lines = format_similar_players(
        pd.DataFrame(
            [
                {
                    "player_name": "Robert Andrich",
                    "team_name": "Bayer Leverkusen",
                    "similarity": 0.932,
                }
            ]
        )
    )

    assert lines == ["Robert Andrich | Bayer Leverkusen | similarity 0.932"]


def test_format_similar_players_can_include_explanations(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 100,
                "carries_per_90": 40,
                "minutes_played": 90,
            },
            {
                "player_id": 2,
                "player_name": "Robert Andrich",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted_per_90": 96,
                "carries_per_90": 20,
                "minutes_played": 90,
            },
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)
    players = pd.DataFrame(
        [
            {
                "player_name": "Robert Andrich",
                "team_name": "Bayer Leverkusen",
                "similarity": 0.932,
            }
        ]
    )

    explanations = explain_similar_players(
        ProjectPaths.from_root(tmp_path),
        player="Xhaka",
        players=players,
    )
    confidence = evaluate_similar_player_confidence(
        ProjectPaths.from_root(tmp_path),
        player="Xhaka",
        players=players,
        same_position=True,
    )
    lines = format_similar_players_with_explanations(
        players,
        explanations=explanations,
        confidence=confidence,
    )

    assert lines == [
        "Robert Andrich | Bayer Leverkusen | similarity 0.932",
        "  Shared traits:",
        "  - similar pass volume",
        "  Differences:",
        "  - Granit Xhaka has higher carry volume",
        "  Confidence: high",
        "  Limitations:",
        "  - match-level sample only",
        "  - based on the current generated feature matrix",
        "  - same broad-position filter applied",
    ]
