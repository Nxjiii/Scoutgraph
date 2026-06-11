from pathlib import Path

import pandas as pd
import pytest

from scoutgraph.identity.team_identity import build_team_identity, format_team_identity
from scoutgraph.storage.paths import ProjectPaths


def test_build_team_identity_labels_possession_attacking_side(tmp_path: Path) -> None:
    _write_team_features(
        tmp_path,
        [
            {
                "team_id": 10,
                "team_name": "Bayer Leverkusen",
                "passes_attempted": 650,
                "pass_completion_pct": 89.7,
                "progressive_passes": 150,
                "carries": 587,
                "progressive_carries": 42,
                "shots": 20,
                "xg": 3.003,
            },
            {
                "team_id": 20,
                "team_name": "Werder Bremen",
                "passes_attempted": 521,
                "pass_completion_pct": 85.6,
                "progressive_passes": 155,
                "carries": 435,
                "progressive_carries": 35,
                "shots": 7,
                "xg": 0.683,
            },
        ],
    )

    identity = build_team_identity(ProjectPaths.from_root(tmp_path), team="Leverkusen")

    assert identity.labels == (
        "high-possession side",
        "secure possession side",
        "active carrying side",
        "progressive carrying side",
        "high-shot side",
        "strong shot creation side",
    )
    assert identity.summary == (
        "Bayer Leverkusen profiles as a possession-heavy attacking side in the current "
        "team sample, with secure possession side, active carrying side, progressive "
        "carrying side, and high-shot side."
    )


def test_build_team_identity_returns_balanced_profile_without_high_traits(
    tmp_path: Path,
) -> None:
    _write_team_features(
        tmp_path,
        [
            _team_row("Example FC", team_id=10),
        ],
    )

    identity = build_team_identity(ProjectPaths.from_root(tmp_path), team="Example")

    assert identity.labels == ()
    assert identity.summary == "Example FC profiles as a balanced side in the current team sample."


def test_format_team_identity_returns_readable_lines(tmp_path: Path) -> None:
    _write_team_features(
        tmp_path,
        [
            _team_row("High Shot FC", team_id=10, shots=12, xg=2.0),
            _team_row("Quiet FC", team_id=20, shots=2, xg=0.2),
        ],
    )

    identity = build_team_identity(ProjectPaths.from_root(tmp_path), team="High Shot")

    assert format_team_identity(identity) == [
        "High Shot FC",
        "",
        "Labels:",
        "- high-shot side",
        "- strong shot creation side",
        "",
        "Summary:",
        "High Shot FC profiles as an attack-minded side in the current "
        "team sample, with high-shot side.",
    ]


def test_build_team_identity_rejects_ambiguous_team_name(tmp_path: Path) -> None:
    _write_team_features(
        tmp_path,
        [
            _team_row("United One", team_id=10),
            _team_row("United Two", team_id=20),
        ],
    )

    with pytest.raises(ValueError, match="Multiple matches found"):
        build_team_identity(ProjectPaths.from_root(tmp_path), team="United")


def _write_team_features(tmp_path: Path, rows: list[dict]) -> None:
    processed_root = tmp_path / "data" / "processed" / "statsbomb"
    processed_root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(processed_root / "team_features.parquet", index=False)


def _team_row(
    team_name: str,
    *,
    team_id: int,
    passes: int = 0,
    pass_completion: float = 0.0,
    progressive_passes: int = 0,
    carries: int = 0,
    progressive_carries: int = 0,
    shots: int = 0,
    xg: float = 0.0,
) -> dict:
    return {
        "team_id": team_id,
        "team_name": team_name,
        "passes_attempted": passes,
        "pass_completion_pct": pass_completion,
        "progressive_passes": progressive_passes,
        "carries": carries,
        "progressive_carries": progressive_carries,
        "shots": shots,
        "xg": xg,
    }
