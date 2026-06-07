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
                "player_name": "Granit Xhaka",
                "team_name": "Bayer Leverkusen",
                "minutes_played": 76.78,
                "passes_attempted_per_90": 99.6,
                "progressive_passes_per_90": 21.1,
                "carries_per_90": 89.1,
                "progressive_carries_per_90": 4.7,
                "shots_per_90": 3.5,
                "xg_per_90": 0.12,
                "pass_completion_pct": 91.8,
            }
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
                "player_name": "Exequiel Palacios",
                "team_name": "Bayer Leverkusen",
                "minutes_played": 13.08,
                "passes_attempted_per_90": 117.0,
                "progressive_passes_per_90": 13.8,
                "carries_per_90": 117.0,
                "progressive_carries_per_90": 6.9,
                "shots_per_90": 6.9,
                "xg_per_90": 0.47,
                "pass_completion_pct": 76.5,
            }
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
            _minimal_row("Alex One"),
            _minimal_row("Alex Two"),
        ],
    )

    with pytest.raises(ValueError, match="Multiple matches found"):
        build_player_identity(ProjectPaths.from_root(tmp_path), player="Alex")


def build_player_identity_from_row(tmp_path: Path, row: dict) -> object:
    _write_player_features(tmp_path, [row])
    return build_player_identity(ProjectPaths.from_root(tmp_path), player=row["player_name"])


def _write_player_features(tmp_path: Path, rows: list[dict]) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(processed_root / "player_features.parquet", index=False)


def _minimal_row(player_name: str) -> dict:
    return {
        "player_name": player_name,
        "team_name": "Example Team",
        "minutes_played": 90.0,
        "passes_attempted_per_90": 0.0,
        "progressive_passes_per_90": 0.0,
        "carries_per_90": 0.0,
        "progressive_carries_per_90": 0.0,
        "shots_per_90": 0.0,
        "xg_per_90": 0.0,
        "pass_completion_pct": 0.0,
    }
