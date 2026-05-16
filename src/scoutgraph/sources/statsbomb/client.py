import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from scoutgraph.storage.paths import ProjectPaths


STATSBOMB_BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


@dataclass(frozen=True)
class StatsBombSample:
    """Known small sample used while building the ingestion layer."""

    competition_id: int = 9
    season_id: int = 281
    match_id: int = 3895302


@dataclass(frozen=True)
class StatsBombSampleSummary:
    competition_name: str
    season_name: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    match_id: int
    event_count: int
    lineup_team_count: int


class StatsBombOpenDataClient:
    """Download and inspect StatsBomb Open Data JSON files."""

    def __init__(self, paths: ProjectPaths, base_url: str = STATSBOMB_BASE_URL) -> None:
        self.paths = paths
        self.base_url = base_url.rstrip("/")
        self.raw_root = paths.raw_data / "statsbomb"

    def fetch_sample(self, sample: StatsBombSample = StatsBombSample()) -> StatsBombSampleSummary:
        """Download the starter sample and return a human-readable summary."""
        self.paths.ensure()

        competitions = self.fetch_json("competitions.json")
        matches = self.fetch_json(f"matches/{sample.competition_id}/{sample.season_id}.json")
        events = self.fetch_json(f"events/{sample.match_id}.json")
        lineups = self.fetch_json(f"lineups/{sample.match_id}.json")

        competition = self._find_competition(
            competitions,
            competition_id=sample.competition_id,
            season_id=sample.season_id,
        )
        match = self._find_match(matches, match_id=sample.match_id)

        return StatsBombSampleSummary(
            competition_name=competition["competition_name"],
            season_name=competition["season_name"],
            home_team=match["home_team"]["home_team_name"],
            away_team=match["away_team"]["away_team_name"],
            home_score=match["home_score"],
            away_score=match["away_score"],
            match_id=sample.match_id,
            event_count=len(events),
            lineup_team_count=len(lineups),
        )

    def fetch_json(self, relative_path: str) -> Any:
        """Load a StatsBomb JSON file from local cache or download it."""
        local_path = self.local_path(relative_path)
        if not local_path.exists():
            self.download_file(relative_path, local_path)

        with local_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def local_path(self, relative_path: str) -> Path:
        return self.raw_root / relative_path

    def download_file(self, relative_path: str, local_path: Path) -> None:
        url = f"{self.base_url}/{relative_path}"
        local_path.parent.mkdir(parents=True, exist_ok=True)

        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        local_path.write_bytes(response.content)

    @staticmethod
    def _find_competition(
        competitions: list[dict[str, Any]],
        *,
        competition_id: int,
        season_id: int,
    ) -> dict[str, Any]:
        for competition in competitions:
            if (
                competition["competition_id"] == competition_id
                and competition["season_id"] == season_id
            ):
                return competition
        raise ValueError(f"Competition {competition_id}, season {season_id} was not found")

    @staticmethod
    def _find_match(matches: list[dict[str, Any]], *, match_id: int) -> dict[str, Any]:
        for match in matches:
            if match["match_id"] == match_id:
                return match
        raise ValueError(f"Match {match_id} was not found")

