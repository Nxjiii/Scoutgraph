from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from scoutgraph.api.app import create_app


def test_player_identity_endpoint_returns_identity_payload(tmp_path: Path) -> None:
    _write_player_identity_inputs(
        tmp_path,
        [
            {
                "player_id": 100,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "position_group": "midfielder",
                "minutes_played": 90.0,
                "passes_attempted_per_90": 100.0,
                "progressive_passes_per_90": 20.0,
                "carries_per_90": 80.0,
                "progressive_carries_per_90": 0.0,
                "shots_per_90": 3.0,
                "xg_per_90": 0.0,
                "pass_completion_pct": 90.0,
            },
            _minimal_player("Example Midfielder", player_id=101),
            _minimal_player("Example Midfielder 2", player_id=102),
            _minimal_player("Example Midfielder 3", player_id=103),
        ],
    )
    client = TestClient(create_app(tmp_path))

    response = client.get("/players/Granit%20Xhaka/identity")

    assert response.status_code == 200
    assert response.json() == {
        "player_name": "Granit Xhaka",
        "team_name": "Bayer Leverkusen",
        "position_group": "midfielder",
        "labels": [
            "high-volume passer",
            "progressive passer",
            "active ball carrier",
            "frequent shooter",
            "secure passer",
        ],
        "summary": (
            "Granit Xhaka profiles as a ball-progressing playmaker, with progressive "
            "passer, active ball carrier, frequent shooter, and secure passer."
        ),
    }


def test_player_identity_endpoint_returns_404_for_unknown_player(tmp_path: Path) -> None:
    _write_player_identity_inputs(
        tmp_path,
        [
            _minimal_player("Known Player", player_id=100),
        ],
    )
    client = TestClient(create_app(tmp_path))

    response = client.get("/players/Missing/identity")

    assert response.status_code == 404
    assert response.json()["detail"] == "No player found matching 'Missing'."


def _write_player_identity_inputs(tmp_path: Path, rows: list[dict]) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(processed_root / "player_features.parquet", index=False)
    pd.DataFrame(
        [
            {
                "player_id": row["player_id"],
                "team_id": row["team_id"],
                "position_id": _position_id(row["position_group"]),
            }
            for row in rows
        ]
    ).to_parquet(processed_root / "player_positions.parquet", index=False)


def _minimal_player(
    player_name: str,
    *,
    player_id: int,
    position_group: str = "midfielder",
) -> dict:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "team_id": 10,
        "team_name": "Example Team",
        "position_group": position_group,
        "minutes_played": 90.0,
        "passes_attempted_per_90": 0.0,
        "progressive_passes_per_90": 0.0,
        "carries_per_90": 0.0,
        "progressive_carries_per_90": 0.0,
        "shots_per_90": 0.0,
        "xg_per_90": 0.0,
        "pass_completion_pct": 0.0,
    }


def _position_id(position_group: str) -> int:
    return {
        "goalkeeper": 1,
        "defender": 4,
        "midfielder": 9,
        "forward": 23,
    }[position_group]
