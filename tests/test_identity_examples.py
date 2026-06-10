from scoutgraph.identity import examples as identity_examples
from scoutgraph.identity.examples import (
    IdentityExample,
    IdentityExampleResult,
    format_identity_example_results,
    run_known_identity_examples,
)
from scoutgraph.identity.player_identity import PlayerIdentity
from scoutgraph.storage.paths import ProjectPaths


def test_run_known_identity_examples_passes_when_expectations_match(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_build_player_identity(paths, *, player):
        return PlayerIdentity(
            player_name=player,
            team_name="Example Team",
            position_group="midfielder",
            labels=("progressive passer", "active ball carrier"),
            summary="Target profiles as a ball-progressing playmaker.",
        )

    monkeypatch.setattr(
        identity_examples,
        "build_player_identity",
        fake_build_player_identity,
    )

    results = run_known_identity_examples(
        ProjectPaths.from_root(tmp_path),
        examples=(
            IdentityExample(
                player="Target Player",
                expected_labels=("progressive passer",),
                absent_labels=("shooting threat",),
                expected_summary_text=("ball-progressing playmaker",),
            ),
        ),
    )

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].notes == ("Expected identity traits were present.",)


def test_run_known_identity_examples_fails_for_missing_expected_label(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_build_player_identity(paths, *, player):
        return PlayerIdentity(
            player_name=player,
            team_name="Example Team",
            position_group="forward",
            labels=("frequent shooter",),
            summary="Target profiles as a shooting-focused attacker.",
        )

    monkeypatch.setattr(
        identity_examples,
        "build_player_identity",
        fake_build_player_identity,
    )

    results = run_known_identity_examples(
        ProjectPaths.from_root(tmp_path),
        examples=(
            IdentityExample(
                player="Target Player",
                expected_labels=("shooting threat",),
            ),
        ),
    )

    assert results[0].passed is False
    assert results[0].notes == ("Missing expected label: shooting threat.",)


def test_run_known_identity_examples_fails_for_unexpected_label(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_build_player_identity(paths, *, player):
        return PlayerIdentity(
            player_name=player,
            team_name="Example Team",
            position_group="midfielder",
            labels=("low-minute sample",),
            summary="Treat this profile cautiously because the sample is low-minute.",
        )

    monkeypatch.setattr(
        identity_examples,
        "build_player_identity",
        fake_build_player_identity,
    )

    results = run_known_identity_examples(
        ProjectPaths.from_root(tmp_path),
        examples=(
            IdentityExample(
                player="Target Player",
                expected_labels=(),
                absent_labels=("low-minute sample",),
            ),
        ),
    )

    assert results[0].passed is False
    assert results[0].notes == ("Unexpected label present: low-minute sample.",)


def test_format_identity_example_results_returns_readable_lines() -> None:
    lines = format_identity_example_results(
        [
            IdentityExampleResult(
                player="Target Player",
                passed=True,
                labels=("progressive passer", "active ball carrier"),
                notes=("Expected identity traits were present.",),
            )
        ]
    )

    assert lines == [
        "PASS | Target Player | labels: progressive passer, active ball carrier",
        "  - Expected identity traits were present.",
    ]
