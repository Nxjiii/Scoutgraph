from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.identity.player_identity import build_player_identity, format_player_identity
from scoutgraph.storage.paths import ProjectPaths


def test_build_player_identity_labels_ball_progressing_playmaker(tmp_path: Path) -> None:
    _write_player_features(
        tmp_path,
        [
            {
                "player_id": 100,
                "player_name": "Granit Xhaka",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "position_group": "midfielder",
                "minutes_played": 76.78,
                "passes_attempted_per_90": 99.6,
                "progressive_passes_per_90": 21.1,
                "carries_per_90": 89.1,
                "progressive_carries_per_90": 4.7,
                "shots_per_90": 3.5,
                "xg_per_90": 0.12,
                "pass_completion_pct": 91.8,
            },
            _minimal_row(
                "Example Midfielder",
                player_id=101,
                position_group="midfielder",
                progressive_carries=7.0,
                xg=0.2,
            ),
            _minimal_row(
                "Example Midfielder 2",
                player_id=102,
                position_group="midfielder",
                progressive_carries=6.0,
                xg=0.15,
            ),
            _minimal_row("Example Midfielder 3", player_id=103, position_group="midfielder"),
        ],
    )

    identity = build_player_identity(ProjectPaths.from_root(tmp_path), player="Xhaka")

    assert identity.labels == (
        "high-volume passer",
        "progressive passer",
        "active ball carrier",
        "frequent shooter",
        "secure passer",
    )
    assert identity.summary == (
        "Granit Xhaka profiles as a ball-progressing playmaker, with progressive passer, "
        "active ball carrier, frequent shooter, and secure passer."
    )


def test_build_player_identity_flags_low_minute_sample(tmp_path: Path) -> None:
    _write_player_features(
        tmp_path,
        [
            {
                "player_id": 100,
                "player_name": "Exequiel Palacios",
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "position_group": "midfielder",
                "minutes_played": 13.08,
                "passes_attempted_per_90": 117.0,
                "progressive_passes_per_90": 13.8,
                "carries_per_90": 117.0,
                "progressive_carries_per_90": 6.9,
                "shots_per_90": 6.9,
                "xg_per_90": 0.47,
                "pass_completion_pct": 76.5,
            },
            _minimal_row("Example Midfielder", player_id=101, position_group="midfielder"),
            _minimal_row("Example Midfielder 2", player_id=102, position_group="midfielder"),
            _minimal_row("Example Midfielder 3", player_id=103, position_group="midfielder"),
        ],
    )

    identity = build_player_identity(ProjectPaths.from_root(tmp_path), player="Palacios")

    assert identity.labels[0] == "low-minute sample"
    assert identity.summary.endswith(
        "Treat this profile cautiously because the sample is low-minute."
    )


def test_format_player_identity_returns_readable_lines(tmp_path: Path) -> None:
    identity = build_player_identity_from_row(
        tmp_path,
        {
            "player_name": "Victor Okoh Boniface",
            "position_group": "forward",
            "team_name": "Bayer Leverkusen",
            "minutes_played": 61.42,
            "passes_attempted_per_90": 22.0,
            "progressive_passes_per_90": 2.9,
            "carries_per_90": 20.5,
            "progressive_carries_per_90": 1.5,
            "shots_per_90": 2.9,
            "xg_per_90": 1.62,
            "pass_completion_pct": 73.3,
        }
    )

    assert format_player_identity(identity) == [
        "Victor Okoh Boniface | Bayer Leverkusen",
        "",
        "Labels:",
        "- shooting threat",
        "",
        "Summary:",
        "Victor Okoh Boniface profiles as a shooting-focused attacker.",
    ]


def test_build_player_identity_rejects_ambiguous_name(tmp_path: Path) -> None:
    _write_player_features(
        tmp_path,
        [
            _minimal_row("Alex One", player_id=100),
            _minimal_row("Alex Two", player_id=200),
        ],
    )

    with pytest.raises(ValueError, match="Multiple matches found"):
        build_player_identity(ProjectPaths.from_root(tmp_path), player="Alex")


def test_build_player_identity_requires_position_context(tmp_path: Path) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True, exist_ok=True)
    row = _minimal_row("No Position", player_id=100)
    row.pop("position_group")
    pd.DataFrame([row]).to_parquet(
        processed_root / "player_features.parquet",
        index=False,
    )
    pd.DataFrame(columns=["player_id", "team_id", "position_id"]).to_parquet(
        processed_root / "player_positions.parquet",
        index=False,
    )

    with pytest.raises(ValueError, match="No position group found"):
        build_player_identity(ProjectPaths.from_root(tmp_path), player="No Position")


def test_build_player_identity_uses_position_aware_percentiles(tmp_path: Path) -> None:
    _write_player_features(
        tmp_path,
        [
            _minimal_row("Quiet Defender", player_id=100, position_group="defender", shots=1),
            _minimal_row("Normal Defender", player_id=101, position_group="defender", shots=2),
            _minimal_row("Shooting Defender", player_id=102, position_group="defender", shots=3),
            _minimal_row("Extreme Defender", player_id=103, position_group="defender", shots=4),
            _minimal_row("Quiet Forward", player_id=200, position_group="forward", shots=1),
            _minimal_row("Normal Forward", player_id=201, position_group="forward", shots=3),
            _minimal_row("Active Forward", player_id=202, position_group="forward", shots=5),
            _minimal_row("Extreme Forward", player_id=203, position_group="forward", shots=7),
        ],
    )

    defender = build_player_identity(ProjectPaths.from_root(tmp_path), player="Shooting Defender")
    forward = build_player_identity(ProjectPaths.from_root(tmp_path), player="Normal Forward")

    assert defender.position_group == "defender"
    assert defender.labels == ("frequent shooter",)
    assert forward.position_group == "forward"
    assert "frequent shooter" not in forward.labels


def build_player_identity_from_row(tmp_path: Path, row: dict) -> object:
    _write_player_features(
        tmp_path,
        [
            row,
            _minimal_row(
                "Example Peer 1",
                player_id=101,
                position_group=row["position_group"],
                passes=40.0,
                progressive_passes=5.0,
                carries=30.0,
                progressive_carries=3.0,
                shots=3.5,
                xg=0.4,
                pass_completion=80.0,
            ),
            _minimal_row(
                "Example Peer 2",
                player_id=102,
                position_group=row["position_group"],
                passes=35.0,
                progressive_passes=4.0,
                carries=28.0,
                progressive_carries=2.0,
                shots=3.2,
                xg=0.5,
                pass_completion=82.0,
            ),
            _minimal_row(
                "Example Peer 3",
                player_id=103,
                position_group=row["position_group"],
                passes=30.0,
                progressive_passes=3.0,
                carries=25.0,
                progressive_carries=2.0,
                shots=3.1,
                xg=0.3,
                pass_completion=78.0,
            ),
        ],
    )
    return build_player_identity(ProjectPaths.from_root(tmp_path), player=row["player_name"])


def _write_player_features(tmp_path: Path, rows: list[dict]) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True, exist_ok=True)
    normalized_rows = [_normalize_row(index, row) for index, row in enumerate(rows)]
    pd.DataFrame(normalized_rows).to_parquet(
        processed_root / "player_features.parquet",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "player_id": row["player_id"],
                "team_id": row["team_id"],
                "position_id": _position_id(row["position_group"]),
            }
            for row in normalized_rows
        ]
    ).to_parquet(processed_root / "player_positions.parquet", index=False)


def _normalize_row(index: int, row: dict) -> dict:
    normalized = _minimal_row(
        row.get("player_name", f"Example Player {index}"),
        player_id=row.get("player_id", index + 1),
        team_id=row.get("team_id", 10),
        position_group=row.get("position_group", "midfielder"),
    )
    normalized.update(row)
    return normalized


def _minimal_row(
    player_name: str,
    *,
    player_id: int = 1,
    team_id: int = 10,
    position_group: str = "midfielder",
    passes: float = 0.0,
    progressive_passes: float = 0.0,
    carries: float = 0.0,
    progressive_carries: float = 0.0,
    shots: float = 0.0,
    xg: float = 0.0,
    pass_completion: float = 0.0,
) -> dict:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "team_id": team_id,
        "team_name": "Example Team",
        "position_group": position_group,
        "minutes_played": 90.0,
        "passes_attempted_per_90": passes,
        "progressive_passes_per_90": progressive_passes,
        "carries_per_90": carries,
        "progressive_carries_per_90": progressive_carries,
        "shots_per_90": shots,
        "xg_per_90": xg,
        "pass_completion_pct": pass_completion,
    }


def _position_id(position_group: str) -> int:
    return {
        "goalkeeper": 1,
        "defender": 4,
        "midfielder": 9,
        "forward": 23,
    }[position_group]
