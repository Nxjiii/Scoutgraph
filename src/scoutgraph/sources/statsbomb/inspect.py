from collections import Counter
from dataclasses import dataclass
import json
from typing import Any

from scoutgraph.sources.statsbomb.client import StatsBombOpenDataClient, StatsBombSample


@dataclass(frozen=True)
class TeamLineupSummary:
    team_name: str
    player_count: int
    first_players: list[str]


@dataclass(frozen=True)
class PassEventSummary:
    event_id: str
    player_name: str
    team_name: str
    location: list[float]
    recipient_name: str | None
    end_location: list[float] | None
    outcome_name: str


@dataclass(frozen=True)
class StatsBombInspectionSummary:
    event_count: int
    event_type_counts: list[tuple[str, int]]
    lineups: list[TeamLineupSummary]
    first_pass: PassEventSummary | None


def inspect_sample(
    client: StatsBombOpenDataClient,
    sample: StatsBombSample = StatsBombSample(),
) -> StatsBombInspectionSummary:
    """Summarize the cached raw StatsBomb sample without normalizing it."""
    events = client.fetch_json(f"events/{sample.match_id}.json")
    lineups = client.fetch_json(f"lineups/{sample.match_id}.json")

    event_type_counts = Counter(event["type"]["name"] for event in events)

    return StatsBombInspectionSummary(
        event_count=len(events),
        event_type_counts=event_type_counts.most_common(),
        lineups=[_summarize_team_lineup(team) for team in lineups],
        first_pass=_first_pass_event(events),
    )


def get_raw_event(
    client: StatsBombOpenDataClient,
    *,
    match_id: int = StatsBombSample().match_id,
    event_id: str | None = None,
    event_type: str | None = "Pass",
) -> dict[str, Any]:
    """Return one raw StatsBomb event for manual inspection."""
    events = client.fetch_json(f"events/{match_id}.json")

    for event in events:
        if event_id is not None and event["id"] == event_id:
            return event
        if event_id is None and event_type is not None and event["type"]["name"] == event_type:
            return event

    if event_id is not None:
        raise ValueError(f"Event {event_id} was not found in match {match_id}")
    raise ValueError(f"No event of type {event_type} was found in match {match_id}")


def format_raw_event(event: dict[str, Any]) -> str:
    """Pretty-print a raw event without changing its source shape."""
    return json.dumps(event, ensure_ascii=False, indent=2)


def _summarize_team_lineup(team: dict[str, Any]) -> TeamLineupSummary:
    players = team["lineup"]
    return TeamLineupSummary(
        team_name=team["team_name"],
        player_count=len(players),
        first_players=[player["player_name"] for player in players[:5]],
    )


def _first_pass_event(events: list[dict[str, Any]]) -> PassEventSummary | None:
    for event in events:
        if event["type"]["name"] != "Pass":
            continue

        pass_data = event["pass"]
        return PassEventSummary(
            event_id=event["id"],
            player_name=event["player"]["name"],
            team_name=event["team"]["name"],
            location=event["location"],
            recipient_name=pass_data.get("recipient", {}).get("name"),
            end_location=pass_data.get("end_location"),
            outcome_name=pass_data.get("outcome", {}).get("name", "Complete"),
        )

    return None
