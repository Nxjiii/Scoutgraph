import json

import pytest

from scoutgraph.sources.statsbomb.inspect import (
    _first_pass_event,
    _summarize_team_lineup,
    format_raw_event,
    get_raw_event,
)


class FakeStatsBombClient:
    def __init__(self, events: list[dict]) -> None:
        self.events = events

    def fetch_json(self, relative_path: str) -> list[dict]:
        return self.events


def test_summarize_team_lineup_counts_players_and_keeps_first_names() -> None:
    summary = _summarize_team_lineup(
        {
            "team_name": "Bayer Leverkusen",
            "lineup": [
                {"player_name": "Granit Xhaka"},
                {"player_name": "Florian Wirtz"},
                {"player_name": "Victor Boniface"},
                {"player_name": "Jonathan Tah"},
                {"player_name": "Jeremie Frimpong"},
                {"player_name": "Alejandro Grimaldo"},
            ],
        }
    )

    assert summary.team_name == "Bayer Leverkusen"
    assert summary.player_count == 6
    assert summary.first_players == [
        "Granit Xhaka",
        "Florian Wirtz",
        "Victor Boniface",
        "Jonathan Tah",
        "Jeremie Frimpong",
    ]


def test_first_pass_event_extracts_common_pass_fields() -> None:
    summary = _first_pass_event(
        [
            {"type": {"name": "Starting XI"}},
            {
                "id": "pass-1",
                "type": {"name": "Pass"},
                "player": {"name": "Granit Xhaka"},
                "team": {"name": "Bayer Leverkusen"},
                "location": [54.2, 36.1],
                "pass": {
                    "recipient": {"name": "Florian Wirtz"},
                    "end_location": [72.8, 41.4],
                },
            },
        ]
    )

    assert summary is not None
    assert summary.event_id == "pass-1"
    assert summary.player_name == "Granit Xhaka"
    assert summary.team_name == "Bayer Leverkusen"
    assert summary.location == [54.2, 36.1]
    assert summary.recipient_name == "Florian Wirtz"
    assert summary.end_location == [72.8, 41.4]
    assert summary.outcome_name == "Complete"


def test_first_pass_event_returns_none_when_no_pass_exists() -> None:
    assert _first_pass_event([{"type": {"name": "Carry"}}]) is None


def test_get_raw_event_returns_first_event_of_type() -> None:
    event = get_raw_event(
        FakeStatsBombClient(
            [
                {"id": "carry-1", "type": {"name": "Carry"}},
                {"id": "pass-1", "type": {"name": "Pass"}},
            ]
        )
    )

    assert event["id"] == "pass-1"


def test_get_raw_event_prefers_event_id_when_provided() -> None:
    event = get_raw_event(
        FakeStatsBombClient(
            [
                {"id": "pass-1", "type": {"name": "Pass"}},
                {"id": "pass-2", "type": {"name": "Pass"}},
            ]
        ),
        event_id="pass-2",
    )

    assert event["id"] == "pass-2"


def test_get_raw_event_raises_when_event_is_missing() -> None:
    with pytest.raises(ValueError, match="Event missing was not found"):
        get_raw_event(FakeStatsBombClient([]), event_id="missing")


def test_format_raw_event_keeps_source_fields_as_json() -> None:
    formatted = format_raw_event({"player": {"name": "Lukáš Hrádecký"}})

    assert json.loads(formatted) == {"player": {"name": "Lukáš Hrádecký"}}
