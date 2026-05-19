from scoutgraph.sources.statsbomb.discovery import (
    format_competition_option,
    format_match_option,
    list_competitions,
    list_matches,
)


class FakeStatsBombClient:
    def __init__(self, payloads: dict[str, list[dict]]) -> None:
        self.payloads = payloads

    def fetch_json(self, relative_path: str) -> list[dict]:
        return self.payloads[relative_path]


def test_list_competitions_returns_sorted_competition_options() -> None:
    competitions = list_competitions(
        FakeStatsBombClient(
            {
                "competitions.json": [
                    {
                        "competition_id": 2,
                        "season_id": 44,
                        "competition_name": "Premier League",
                        "season_name": "2003/2004",
                        "country_name": "England",
                    },
                    {
                        "competition_id": 9,
                        "season_id": 281,
                        "competition_name": "1. Bundesliga",
                        "season_name": "2023/2024",
                        "country_name": "Germany",
                    },
                ]
            }
        )
    )

    assert competitions[0].competition_name == "1. Bundesliga"
    assert format_competition_option(competitions[0]) == (
        "9/281 | 1. Bundesliga | 2023/2024 | Germany"
    )


def test_list_matches_returns_sorted_match_options() -> None:
    matches = list_matches(
        FakeStatsBombClient(
            {
                "matches/9/281.json": [
                    {
                        "match_id": 2,
                        "match_date": "2024-05-01",
                        "home_team": {"home_team_name": "Team B"},
                        "away_team": {"away_team_name": "Team C"},
                        "home_score": 1,
                        "away_score": 0,
                    },
                    {
                        "match_id": 1,
                        "match_date": "2024-04-14",
                        "home_team": {"home_team_name": "Bayer Leverkusen"},
                        "away_team": {"away_team_name": "Werder Bremen"},
                        "home_score": 5,
                        "away_score": 0,
                    },
                ]
            }
        ),
        competition_id=9,
        season_id=281,
    )

    assert matches[0].match_id == 1
    assert format_match_option(matches[0]) == (
        "1 | 2024-04-14 | Bayer Leverkusen 5-0 Werder Bremen"
    )

