from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from scoutgraph.api.app import create_app


def test_player_search_returns_partial_name_matches(tmp_path: Path) -> None:
    _write_player_inputs(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/players", params={"query": "gran", "limit": 1})

    assert response.status_code == 200
    assert response.json() == [
        {
            "player_id": 1,
            "player_name": "Granit Xhaka",
            "team_id": 10,
            "team_name": "Bayer Leverkusen",
            "position_group": "midfielder",
        }
    ]


def test_player_profile_combines_identity_and_metrics(tmp_path: Path) -> None:
    _write_player_inputs(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/players/Granit%20Xhaka")

    assert response.status_code == 200
    payload = response.json()
    assert payload["player_name"] == "Granit Xhaka"
    assert payload["position_group"] == "midfielder"
    assert payload["summary"].startswith("Granit Xhaka profiles as")
    assert payload["metrics"]["minutes_played"] == 90.0
    assert payload["metrics"]["passes_attempted_per_90"] == 100.0
    assert "player_id" not in payload["metrics"]


def test_player_similarity_returns_explanations_and_confidence(tmp_path: Path) -> None:
    _write_player_inputs(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get(
        "/players/Granit%20Xhaka/similarity",
        params={"same_position": True, "limit": 1},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    result = response.json()[0]
    assert result["player_name"] == "Robert Andrich"
    assert result["position_group"] == "midfielder"
    assert isinstance(result["similarity"], float)
    assert result["shared_traits"]
    assert result["confidence"] in {"low", "medium", "high"}
    assert "same broad-position filter applied" in result["limitations"]


def test_player_profile_returns_404_for_unknown_player(tmp_path: Path) -> None:
    _write_player_inputs(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/players/Missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "No player found matching 'Missing'."


def test_player_search_returns_503_when_feature_data_is_missing(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/players", params={"query": "Xhaka"})

    assert response.status_code == 503
    assert "Player feature matrix not found" in response.json()["detail"]


def _write_player_inputs(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True)
    players = [
        _player(1, "Granit Xhaka", passes=100, progressive_passes=20, carries=30, shots=1),
        _player(2, "Robert Andrich", passes=96, progressive_passes=19, carries=29, shots=1),
        _player(3, "Example Midfielder", passes=45, progressive_passes=5, carries=12, shots=2),
        _player(4, "Example Midfielder 2", passes=30, progressive_passes=2, carries=8, shots=4),
    ]
    pd.DataFrame(players).to_parquet(processed_root / "player_features.parquet", index=False)
    pd.DataFrame(
        [
            {"player_id": player["player_id"], "team_id": player["team_id"], "position_id": 9}
            for player in players
        ]
    ).to_parquet(processed_root / "player_positions.parquet", index=False)


def _player(
    player_id: int,
    name: str,
    *,
    passes: float,
    progressive_passes: float,
    carries: float,
    shots: float,
) -> dict[str, int | float | str]:
    return {
        "player_id": player_id,
        "player_name": name,
        "team_id": 10,
        "team_name": "Bayer Leverkusen",
        "minutes_played": 90.0,
        "passes_attempted_per_90": passes,
        "passes_completed_per_90": passes * 0.9,
        "progressive_passes_per_90": progressive_passes,
        "pass_completion_pct": 90.0,
        "avg_pass_length": 20.0,
        "carries_per_90": carries,
        "progressive_carries_per_90": carries / 3,
        "carries_into_final_third_per_90": carries / 4,
        "carries_into_box_per_90": carries / 10,
        "avg_carry_distance": 6.0,
        "shots_per_90": shots,
        "shots_on_target_per_90": shots / 2,
        "shots_in_box_per_90": shots / 2,
        "goals_per_90": 0.0,
        "xg_per_90": shots / 10,
        "avg_shot_distance": 20.0,
    }
