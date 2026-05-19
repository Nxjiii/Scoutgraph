from pathlib import Path

import pytest

from scoutgraph.sources.statsbomb.client import (
    DEFAULT_SAMPLE_MATCH,
    StatsBombMatchRef,
    StatsBombOpenDataClient,
)
from scoutgraph.storage.paths import ProjectPaths


def test_statsbomb_local_path_uses_raw_statsbomb_folder(tmp_path: Path) -> None:
    client = StatsBombOpenDataClient(ProjectPaths.from_root(tmp_path))

    assert (
        client.local_path("matches/9/281.json")
        == tmp_path / "data" / "raw" / "statsbomb" / "matches" / "9" / "281.json"
    )


def test_statsbomb_sample_summary_uses_cached_json(tmp_path: Path) -> None:
    raw_root = tmp_path / "data" / "raw" / "statsbomb"
    (raw_root / "matches" / "9").mkdir(parents=True)
    (raw_root / "events").mkdir()
    (raw_root / "lineups").mkdir()

    (raw_root / "competitions.json").write_text(
        """
        [
          {
            "competition_id": 9,
            "season_id": 281,
            "competition_name": "1. Bundesliga",
            "season_name": "2023/2024"
          }
        ]
        """,
        encoding="utf-8",
    )
    (raw_root / "matches" / "9" / "281.json").write_text(
        """
        [
          {
            "match_id": 3895302,
            "home_team": {"home_team_name": "Bayer Leverkusen"},
            "away_team": {"away_team_name": "Werder Bremen"},
            "home_score": 5,
            "away_score": 0
          }
        ]
        """,
        encoding="utf-8",
    )
    (raw_root / "events" / "3895302.json").write_text("[{}, {}, {}]", encoding="utf-8")
    (raw_root / "lineups" / "3895302.json").write_text("[{}, {}]", encoding="utf-8")

    client = StatsBombOpenDataClient(ProjectPaths.from_root(tmp_path))
    summary = client.fetch_match(StatsBombMatchRef(competition_id=9, season_id=281, match_id=3895302))

    assert summary.competition_name == "1. Bundesliga"
    assert summary.season_name == "2023/2024"
    assert summary.home_team == "Bayer Leverkusen"
    assert summary.away_team == "Werder Bremen"
    assert summary.home_score == 5
    assert summary.away_score == 0
    assert summary.event_count == 3
    assert summary.lineup_team_count == 2


def test_fetch_sample_uses_default_sample_match(tmp_path: Path) -> None:
    raw_root = tmp_path / "data" / "raw" / "statsbomb"
    (raw_root / "matches" / "9").mkdir(parents=True)
    (raw_root / "events").mkdir()
    (raw_root / "lineups").mkdir()

    (raw_root / "competitions.json").write_text(
        """
        [
          {
            "competition_id": 9,
            "season_id": 281,
            "competition_name": "1. Bundesliga",
            "season_name": "2023/2024"
          }
        ]
        """,
        encoding="utf-8",
    )
    (raw_root / "matches" / "9" / "281.json").write_text(
        """
        [
          {
            "match_id": 3895302,
            "home_team": {"home_team_name": "Bayer Leverkusen"},
            "away_team": {"away_team_name": "Werder Bremen"},
            "home_score": 5,
            "away_score": 0
          }
        ]
        """,
        encoding="utf-8",
    )
    (raw_root / "events" / "3895302.json").write_text("[{}]", encoding="utf-8")
    (raw_root / "lineups" / "3895302.json").write_text("[{}, {}]", encoding="utf-8")

    summary = StatsBombOpenDataClient(ProjectPaths.from_root(tmp_path)).fetch_sample()

    assert summary.match_id == DEFAULT_SAMPLE_MATCH.match_id


def test_statsbomb_sample_summary_raises_for_missing_match(tmp_path: Path) -> None:
    client = StatsBombOpenDataClient(ProjectPaths.from_root(tmp_path))

    with pytest.raises(ValueError, match="Match 3895302 was not found"):
        client._find_match([], match_id=DEFAULT_SAMPLE_MATCH.match_id)
