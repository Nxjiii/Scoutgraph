from dataclasses import dataclass
from typing import Any

from scoutgraph.sources.statsbomb.client import StatsBombOpenDataClient


@dataclass(frozen=True)
class StatsBombCompetitionOption:
    competition_id: int
    season_id: int
    competition_name: str
    season_name: str
    country_name: str | None


@dataclass(frozen=True)
class StatsBombMatchOption:
    match_id: int
    match_date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int


def list_competitions(client: StatsBombOpenDataClient) -> list[StatsBombCompetitionOption]:
    """Return available StatsBomb competition-season options."""
    competitions = client.fetch_json("competitions.json")
    options = [_competition_option(row) for row in competitions]
    return sorted(options, key=lambda option: (option.competition_name, option.season_name))


def list_matches(
    client: StatsBombOpenDataClient,
    *,
    competition_id: int,
    season_id: int,
) -> list[StatsBombMatchOption]:
    """Return matches for one StatsBomb competition-season."""
    matches = client.fetch_json(f"matches/{competition_id}/{season_id}.json")
    options = [_match_option(row) for row in matches]
    return sorted(options, key=lambda option: (option.match_date, option.match_id))


def format_competition_option(option: StatsBombCompetitionOption) -> str:
    return (
        f"{option.competition_id}/{option.season_id} | "
        f"{option.competition_name} | {option.season_name} | {option.country_name}"
    )


def format_match_option(option: StatsBombMatchOption) -> str:
    return (
        f"{option.match_id} | {option.match_date} | "
        f"{option.home_team} {option.home_score}-{option.away_score} {option.away_team}"
    )


def _competition_option(row: dict[str, Any]) -> StatsBombCompetitionOption:
    return StatsBombCompetitionOption(
        competition_id=row["competition_id"],
        season_id=row["season_id"],
        competition_name=row["competition_name"],
        season_name=row["season_name"],
        country_name=row.get("country_name"),
    )


def _match_option(row: dict[str, Any]) -> StatsBombMatchOption:
    return StatsBombMatchOption(
        match_id=row["match_id"],
        match_date=row["match_date"],
        home_team=row["home_team"]["home_team_name"],
        away_team=row["away_team"]["away_team_name"],
        home_score=row["home_score"],
        away_score=row["away_score"],
    )

