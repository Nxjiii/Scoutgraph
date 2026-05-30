from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.similarity.player_similarity import (
    find_similar_players,
    format_similar_players,
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
                "passes_attempted": 100,
                "progressive_passes": 20,
                "carries": 30,
                "shots": 1,
                "xg": 0.1,
            },
            {
                "player_id": 2,
                "player_name": "Robert Andrich",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted": 95,
                "progressive_passes": 18,
                "carries": 28,
                "shots": 1,
                "xg": 0.08,
            },
            {
                "player_id": 3,
                "player_name": "Victor Boniface",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted": 20,
                "progressive_passes": 2,
                "carries": 12,
                "shots": 6,
                "xg": 1.2,
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
                "passes_attempted": 100,
            }
        ]
    ).to_parquet(processed_root / "player_features.parquet", index=False)

    with pytest.raises(ValueError, match="No player found"):
        find_similar_players(ProjectPaths.from_root(tmp_path), player="Saka")


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
