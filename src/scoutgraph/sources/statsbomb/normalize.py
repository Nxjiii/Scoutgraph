from dataclasses import dataclass
from typing import Any

import pandas as pd

from scoutgraph.sources.statsbomb.client import (
    DEFAULT_SAMPLE_MATCH,
    StatsBombMatchRef,
    StatsBombOpenDataClient,
)


@dataclass(frozen=True)
class NormalizedStatsBombMatch:
    competitions: pd.DataFrame
    matches: pd.DataFrame
    teams: pd.DataFrame
    players: pd.DataFrame
    lineups: pd.DataFrame
    player_positions: pd.DataFrame
    events: pd.DataFrame
    pass_events: pd.DataFrame
    carry_events: pd.DataFrame

    def counts(self) -> dict[str, int]:
        return {
            "competitions": len(self.competitions),
            "matches": len(self.matches),
            "teams": len(self.teams),
            "players": len(self.players),
            "lineups": len(self.lineups),
            "player_positions": len(self.player_positions),
            "events": len(self.events),
            "pass_events": len(self.pass_events),
            "carry_events": len(self.carry_events),
        }


def normalize_sample(
    client: StatsBombOpenDataClient,
) -> NormalizedStatsBombMatch:
    """Normalize the cached StatsBomb sample into flat analytical tables."""
    return normalize_match(client, DEFAULT_SAMPLE_MATCH)


def normalize_match(
    client: StatsBombOpenDataClient,
    match_ref: StatsBombMatchRef,
) -> NormalizedStatsBombMatch:
    """Normalize one cached StatsBomb match into flat analytical tables."""
    competitions = client.fetch_json("competitions.json")
    matches = client.fetch_json(f"matches/{match_ref.competition_id}/{match_ref.season_id}.json")
    events = client.fetch_json(f"events/{match_ref.match_id}.json")
    lineups = client.fetch_json(f"lineups/{match_ref.match_id}.json")

    competition = client._find_competition(
        competitions,
        competition_id=match_ref.competition_id,
        season_id=match_ref.season_id,
    )
    match = client._find_match(matches, match_id=match_ref.match_id)

    normalized = NormalizedStatsBombMatch(
        competitions=pd.DataFrame([_competition_row(competition)]),
        matches=pd.DataFrame([_match_row(match)]),
        teams=pd.DataFrame(_team_rows(match, lineups)).drop_duplicates("team_id"),
        players=pd.DataFrame(_player_rows(lineups)).drop_duplicates("player_id"),
        lineups=pd.DataFrame(_lineup_rows(match_ref.match_id, lineups)),
        player_positions=pd.DataFrame(_player_position_rows(match_ref.match_id, lineups)),
        events=pd.DataFrame(_event_rows(match_ref.match_id, events)),
        pass_events=pd.DataFrame(_pass_event_rows(events)),
        carry_events=pd.DataFrame(_carry_event_rows(events)),
    )

    output_root = client.paths.processed_data / "statsbomb"
    output_root.mkdir(parents=True, exist_ok=True)
    for table_name, table in normalized_tables(normalized).items():
        table.to_parquet(output_root / f"{table_name}.parquet", index=False)

    return normalized


def normalize_season(
    client: StatsBombOpenDataClient,
    *,
    competition_id: int,
    season_id: int,
    limit: int | None = None,
) -> NormalizedStatsBombMatch:
    """Normalize cached matches for one StatsBomb competition-season."""
    competitions = client.fetch_json("competitions.json")
    matches = client.fetch_json(f"matches/{competition_id}/{season_id}.json")
    selected_matches = matches[:limit] if limit is not None else matches

    competition = client._find_competition(
        competitions,
        competition_id=competition_id,
        season_id=season_id,
    )

    team_rows: list[dict[str, Any]] = []
    player_rows: list[dict[str, Any]] = []
    lineup_rows: list[dict[str, Any]] = []
    player_position_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    pass_event_rows: list[dict[str, Any]] = []
    carry_event_rows: list[dict[str, Any]] = []

    for match in selected_matches:
        match_id = match["match_id"]
        events = client.fetch_json(f"events/{match_id}.json")
        lineups = client.fetch_json(f"lineups/{match_id}.json")

        team_rows.extend(_team_rows(match, lineups))
        player_rows.extend(_player_rows(lineups))
        lineup_rows.extend(_lineup_rows(match_id, lineups))
        player_position_rows.extend(_player_position_rows(match_id, lineups))
        event_rows.extend(_event_rows(match_id, events))
        pass_event_rows.extend(_pass_event_rows(events))
        carry_event_rows.extend(_carry_event_rows(events))

    normalized = NormalizedStatsBombMatch(
        competitions=pd.DataFrame([_competition_row(competition)]),
        matches=pd.DataFrame([_match_row(match) for match in selected_matches]).drop_duplicates(
            "match_id"
        ),
        teams=pd.DataFrame(team_rows).drop_duplicates("team_id"),
        players=pd.DataFrame(player_rows).drop_duplicates("player_id"),
        lineups=pd.DataFrame(lineup_rows).drop_duplicates(["match_id", "team_id", "player_id"]),
        player_positions=pd.DataFrame(player_position_rows).drop_duplicates(
            ["match_id", "player_id", "position_id", "from_time"]
        ),
        events=pd.DataFrame(event_rows).drop_duplicates("event_id"),
        pass_events=pd.DataFrame(pass_event_rows).drop_duplicates("event_id"),
        carry_events=pd.DataFrame(carry_event_rows).drop_duplicates("event_id"),
    )

    output_root = client.paths.processed_data / "statsbomb"
    output_root.mkdir(parents=True, exist_ok=True)
    for table_name, table in normalized_tables(normalized).items():
        table.to_parquet(output_root / f"{table_name}.parquet", index=False)

    return normalized


def normalized_tables(normalized: NormalizedStatsBombMatch) -> dict[str, pd.DataFrame]:
    return {
        "competitions": normalized.competitions,
        "matches": normalized.matches,
        "teams": normalized.teams,
        "players": normalized.players,
        "lineups": normalized.lineups,
        "player_positions": normalized.player_positions,
        "events": normalized.events,
        "pass_events": normalized.pass_events,
        "carry_events": normalized.carry_events,
    }


def _competition_row(competition: dict[str, Any]) -> dict[str, Any]:
    return {
        "competition_id": competition["competition_id"],
        "season_id": competition["season_id"],
        "competition_name": competition["competition_name"],
        "season_name": competition["season_name"],
        "country_name": competition.get("country_name"),
        "competition_gender": competition.get("competition_gender"),
        "match_available": competition.get("match_available"),
        "match_available_360": competition.get("match_available_360"),
    }


def _match_row(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "match_id": match["match_id"],
        "competition_id": match["competition"]["competition_id"],
        "season_id": match["season"]["season_id"],
        "match_date": match["match_date"],
        "kick_off": match.get("kick_off"),
        "home_team_id": match["home_team"]["home_team_id"],
        "away_team_id": match["away_team"]["away_team_id"],
        "home_score": match["home_score"],
        "away_score": match["away_score"],
        "match_week": match.get("match_week"),
        "stadium_name": _nested_name(match, "stadium"),
        "referee_name": _nested_name(match, "referee"),
    }


def _team_rows(match: dict[str, Any], lineups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        _team_row(
            team_id=match["home_team"]["home_team_id"],
            team_name=match["home_team"]["home_team_name"],
            country_name=_nested_name(match["home_team"], "country"),
        ),
        _team_row(
            team_id=match["away_team"]["away_team_id"],
            team_name=match["away_team"]["away_team_name"],
            country_name=_nested_name(match["away_team"], "country"),
        ),
    ]
    rows.extend(
        _team_row(
            team_id=lineup_team["team_id"],
            team_name=lineup_team["team_name"],
            country_name=None,
        )
        for lineup_team in lineups
    )
    return rows


def _team_row(team_id: int, team_name: str, country_name: str | None) -> dict[str, Any]:
    return {
        "team_id": team_id,
        "team_name": team_name,
        "country_name": country_name,
    }


def _player_rows(lineups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for lineup_team in lineups:
        for player in lineup_team["lineup"]:
            rows.append(
                {
                    "player_id": player["player_id"],
                    "player_name": player["player_name"],
                    "player_nickname": player.get("player_nickname"),
                    "country_name": _nested_name(player, "country"),
                }
            )
    return rows


def _lineup_rows(match_id: int, lineups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for lineup_team in lineups:
        for player in lineup_team["lineup"]:
            rows.append(
                {
                    "match_id": match_id,
                    "team_id": lineup_team["team_id"],
                    "player_id": player["player_id"],
                    "jersey_number": player.get("jersey_number"),
                }
            )
    return rows


def _player_position_rows(match_id: int, lineups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for lineup_team in lineups:
        for player in lineup_team["lineup"]:
            for position in player["positions"]:
                rows.append(
                    {
                        "match_id": match_id,
                        "team_id": lineup_team["team_id"],
                        "player_id": player["player_id"],
                        "position_id": position["position_id"],
                        "position_name": position["position"],
                        "from_time": position["from"],
                        "to_time": position.get("to"),
                        "from_period": position["from_period"],
                        "to_period": position.get("to_period"),
                        "start_reason": position["start_reason"],
                        "end_reason": position["end_reason"],
                    }
                )
    return rows


def _event_rows(match_id: int, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_event_row(match_id, event) for event in events]


def _event_row(match_id: int, event: dict[str, Any]) -> dict[str, Any]:
    location = event.get("location") or [None, None]
    return {
        "event_id": event["id"],
        "match_id": match_id,
        "event_index": event["index"],
        "period": event["period"],
        "timestamp": event["timestamp"],
        "minute": event["minute"],
        "second": event["second"],
        "event_type_id": event["type"]["id"],
        "event_type_name": event["type"]["name"],
        "possession": event["possession"],
        "possession_team_id": event["possession_team"]["id"],
        "possession_team_name": event["possession_team"]["name"],
        "play_pattern_id": event["play_pattern"]["id"],
        "play_pattern_name": event["play_pattern"]["name"],
        "team_id": event["team"]["id"],
        "team_name": event["team"]["name"],
        "player_id": _nested_id(event, "player"),
        "player_name": _nested_name(event, "player"),
        "position_id": _nested_id(event, "position"),
        "position_name": _nested_name(event, "position"),
        "location_x": location[0],
        "location_y": location[1],
        "duration": event.get("duration"),
        "under_pressure": event.get("under_pressure", False),
    }


def _pass_event_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        if event["type"]["name"] != "Pass":
            continue
        rows.append(_pass_event_row(event))
    return rows


def _pass_event_row(event: dict[str, Any]) -> dict[str, Any]:
    pass_data = event["pass"]
    end_location = pass_data.get("end_location") or [None, None]
    outcome = pass_data.get("outcome")

    return {
        "event_id": event["id"],
        "recipient_player_id": _nested_id(pass_data, "recipient"),
        "recipient_player_name": _nested_name(pass_data, "recipient"),
        "length": pass_data.get("length"),
        "angle": pass_data.get("angle"),
        "height_id": _nested_id(pass_data, "height"),
        "height_name": _nested_name(pass_data, "height"),
        "end_location_x": end_location[0],
        "end_location_y": end_location[1],
        "body_part_id": _nested_id(pass_data, "body_part"),
        "body_part_name": _nested_name(pass_data, "body_part"),
        "pass_type_id": _nested_id(pass_data, "type"),
        "pass_type_name": _nested_name(pass_data, "type"),
        "outcome_id": outcome.get("id") if outcome else None,
        "outcome_name": outcome.get("name") if outcome else "Complete",
    }


def _carry_event_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        if event["type"]["name"] != "Carry":
            continue
        rows.append(_carry_event_row(event))
    return rows


def _carry_event_row(event: dict[str, Any]) -> dict[str, Any]:
    carry_data = event["carry"]
    start_location = event.get("location") or [None, None]
    end_location = carry_data.get("end_location") or [None, None]

    return {
        "event_id": event["id"],
        "end_location_x": end_location[0],
        "end_location_y": end_location[1],
        "carry_distance": _distance(start_location, end_location),
    }


def _distance(start_location: list[float | None], end_location: list[float | None]) -> float | None:
    start_x, start_y = start_location
    end_x, end_y = end_location
    if start_x is None or start_y is None or end_x is None or end_y is None:
        return None
    return ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5


def _nested_id(data: dict[str, Any], key: str) -> int | None:
    nested = data.get(key)
    return nested.get("id") if nested else None


def _nested_name(data: dict[str, Any], key: str) -> str | None:
    nested = data.get(key)
    return nested.get("name") if nested else None
