from scoutgraph.sources.statsbomb.normalize import _event_row, _match_row, _pass_event_row


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

