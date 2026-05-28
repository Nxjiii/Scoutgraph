from pathlib import Path

from scoutgraph.sources.statsbomb.normalize import (
    _carry_event_row,
    _event_row,
    _match_row,
    _pass_event_row,
    normalize_season,
)
from scoutgraph.storage.paths import ProjectPaths


def test_match_row_flattens_match_metadata() -> None:
    row = _match_row(
        {
            "match_id": 3895302,
            "competition": {"competition_id": 9},
            "season": {"season_id": 281},
            "match_date": "2024-04-14",
            "kick_off": "17:30:00.000",
            "home_team": {"home_team_id": 904},
            "away_team": {"away_team_id": 176},
            "home_score": 5,
            "away_score": 0,
            "match_week": 29,
            "stadium": {"name": "BayArena"},
            "referee": {"name": "Harm Osmers"},
        }
    )

    assert row == {
        "match_id": 3895302,
        "competition_id": 9,
        "season_id": 281,
        "match_date": "2024-04-14",
        "kick_off": "17:30:00.000",
        "home_team_id": 904,
        "away_team_id": 176,
        "home_score": 5,
        "away_score": 0,
        "match_week": 29,
        "stadium_name": "BayArena",
        "referee_name": "Harm Osmers",
    }


def test_event_row_flattens_common_event_fields() -> None:
    row = _event_row(
        3895302,
        {
            "id": "event-1",
            "index": 5,
            "period": 1,
            "timestamp": "00:00:03.417",
            "minute": 0,
            "second": 3,
            "type": {"id": 30, "name": "Pass"},
            "possession": 2,
            "possession_team": {"id": 176, "name": "Werder Bremen"},
            "play_pattern": {"id": 9, "name": "From Kick Off"},
            "team": {"id": 176, "name": "Werder Bremen"},
            "player": {"id": 34870, "name": "Nick Woltemade"},
            "position": {"id": 22, "name": "Right Center Forward"},
            "location": [61.0, 40.1],
            "duration": 0.453249,
        },
    )

    assert row["event_id"] == "event-1"
    assert row["match_id"] == 3895302
    assert row["event_type_name"] == "Pass"
    assert row["team_name"] == "Werder Bremen"
    assert row["player_name"] == "Nick Woltemade"
    assert row["location_x"] == 61.0
    assert row["location_y"] == 40.1
    assert row["under_pressure"] is False


def test_pass_event_row_flattens_pass_specific_fields() -> None:
    row = _pass_event_row(
        {
            "id": "pass-1",
            "type": {"id": 30, "name": "Pass"},
            "pass": {
                "recipient": {"id": 12299, "name": "Marvin Ducksch"},
                "length": 2.1540658,
                "angle": 2.7610862,
                "height": {"id": 1, "name": "Ground Pass"},
                "end_location": [59.0, 40.9],
                "body_part": {"id": 40, "name": "Right Foot"},
                "type": {"id": 65, "name": "Kick Off"},
            },
        }
    )

    assert row == {
        "event_id": "pass-1",
        "recipient_player_id": 12299,
        "recipient_player_name": "Marvin Ducksch",
        "length": 2.1540658,
        "angle": 2.7610862,
        "height_id": 1,
        "height_name": "Ground Pass",
        "end_location_x": 59.0,
        "end_location_y": 40.9,
        "body_part_id": 40,
        "body_part_name": "Right Foot",
        "pass_type_id": 65,
        "pass_type_name": "Kick Off",
        "outcome_id": None,
        "outcome_name": "Complete",
    }


def test_carry_event_row_flattens_carry_specific_fields() -> None:
    row = _carry_event_row(
        {
            "id": "carry-1",
            "type": {"id": 43, "name": "Carry"},
            "location": [40.0, 30.0],
            "carry": {"end_location": [52.0, 35.0]},
        }
    )

    assert row["event_id"] == "carry-1"
    assert row["end_location_x"] == 52.0
    assert row["end_location_y"] == 35.0
    assert round(row["carry_distance"], 2) == 13.0


def test_normalize_season_combines_matches_and_dedupes_dimensions(tmp_path: Path) -> None:
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
            "match_id": 1,
            "competition": {"competition_id": 9},
            "season": {"season_id": 281},
            "match_date": "2024-01-01",
            "home_team": {"home_team_id": 10, "home_team_name": "Team A"},
            "away_team": {"away_team_id": 20, "away_team_name": "Team B"},
            "home_score": 1,
            "away_score": 0
          },
          {
            "match_id": 2,
            "competition": {"competition_id": 9},
            "season": {"season_id": 281},
            "match_date": "2024-01-08",
            "home_team": {"home_team_id": 10, "home_team_name": "Team A"},
            "away_team": {"away_team_id": 30, "away_team_name": "Team C"},
            "home_score": 2,
            "away_score": 0
          }
        ]
        """,
        encoding="utf-8",
    )

    lineup_payload = """
    [
      {
        "team_id": 10,
        "team_name": "Team A",
        "lineup": [
          {
            "player_id": 100,
            "player_name": "Player One",
            "player_nickname": null,
            "jersey_number": 8,
            "country": {"name": "Germany"},
            "positions": [
              {
                "position_id": 9,
                "position": "Right Defensive Midfield",
                "from": "00:00",
                "to": null,
                "from_period": 1,
                "to_period": null,
                "start_reason": "Starting XI",
                "end_reason": "Final Whistle"
              }
            ]
          }
        ]
      }
    ]
    """
    event_payload = """
    [
      {
        "id": "EVENT_ID",
        "index": 1,
        "period": 1,
        "timestamp": "00:00:01.000",
        "minute": 0,
        "second": 1,
        "type": {"id": 30, "name": "Pass"},
        "possession": 1,
        "possession_team": {"id": 10, "name": "Team A"},
        "play_pattern": {"id": 1, "name": "Regular Play"},
        "team": {"id": 10, "name": "Team A"},
        "player": {"id": 100, "name": "Player One"},
        "position": {"id": 9, "name": "Right Defensive Midfield"},
        "location": [40.0, 30.0],
        "pass": {
          "recipient": {"id": 100, "name": "Player One"},
          "end_location": [42.0, 31.0]
        }
      }
    ]
    """
    (raw_root / "lineups" / "1.json").write_text(lineup_payload, encoding="utf-8")
    (raw_root / "lineups" / "2.json").write_text(lineup_payload, encoding="utf-8")
    (raw_root / "events" / "1.json").write_text(
        event_payload.replace("EVENT_ID", "event-1"),
        encoding="utf-8",
    )
    (raw_root / "events" / "2.json").write_text(
        event_payload.replace("EVENT_ID", "event-2"),
        encoding="utf-8",
    )

    normalized = normalize_season(
        client=FakeStatsBombClient(ProjectPaths.from_root(tmp_path)),
        competition_id=9,
        season_id=281,
        limit=2,
    )

    assert normalized.counts()["matches"] == 2
    assert normalized.counts()["teams"] == 3
    assert normalized.counts()["players"] == 1
    assert normalized.counts()["lineups"] == 2
    assert normalized.counts()["events"] == 2
    assert normalized.counts()["pass_events"] == 2


class FakeStatsBombClient:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    def fetch_json(self, relative_path: str):
        import json

        with (self.paths.raw_data / "statsbomb" / relative_path).open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    _find_competition = staticmethod(
        lambda competitions, *, competition_id, season_id: next(
            row
            for row in competitions
            if row["competition_id"] == competition_id and row["season_id"] == season_id
        )
    )
