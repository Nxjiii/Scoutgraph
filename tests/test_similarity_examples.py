import pandas as pd

from scoutgraph.similarity import examples as similarity_examples
from scoutgraph.similarity.examples import (
    SimilarityExample,
    format_similarity_example_results,
    run_known_similarity_examples,
)
from scoutgraph.storage.paths import ProjectPaths


def test_run_known_similarity_examples_passes_when_expected_player_is_returned(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_find_similar_players(paths, *, player, limit, same_position):
        return pd.DataFrame(
            [
                {
                    "player_name": "Expected Player",
                    "team_name": "Example Team",
                    "similarity": 0.8,
                }
            ]
        )

    monkeypatch.setattr(
        similarity_examples,
        "find_similar_players",
        fake_find_similar_players,
    )

    results = run_known_similarity_examples(
        ProjectPaths.from_root(tmp_path),
        examples=(
            SimilarityExample(
                player="Target Player",
                expected_player="Expected Player",
                minimum_similarity=0.75,
            ),
        ),
    )

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].rank == 1
    assert results[0].similarity == 0.8


def test_run_known_similarity_examples_fails_when_expected_player_is_missing(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_find_similar_players(paths, *, player, limit, same_position):
        return pd.DataFrame(
            [
                {
                    "player_name": "Different Player",
                    "team_name": "Example Team",
                    "similarity": 0.8,
                }
            ]
        )

    monkeypatch.setattr(
        similarity_examples,
        "find_similar_players",
        fake_find_similar_players,
    )

    results = run_known_similarity_examples(
        ProjectPaths.from_root(tmp_path),
        examples=(
            SimilarityExample(
                player="Target Player",
                expected_player="Expected Player",
            ),
        ),
    )

    assert results[0].passed is False
    assert results[0].rank is None
    assert results[0].notes == (
        "Expected player was not returned in the configured result limit.",
    )


def test_run_known_similarity_examples_fails_below_similarity_threshold(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_find_similar_players(paths, *, player, limit, same_position):
        return pd.DataFrame(
            [
                {
                    "player_name": "Expected Player",
                    "team_name": "Example Team",
                    "similarity": 0.2,
                }
            ]
        )

    monkeypatch.setattr(
        similarity_examples,
        "find_similar_players",
        fake_find_similar_players,
    )

    results = run_known_similarity_examples(
        ProjectPaths.from_root(tmp_path),
        examples=(
            SimilarityExample(
                player="Target Player",
                expected_player="Expected Player",
                minimum_similarity=0.5,
            ),
        ),
    )

    assert results[0].passed is False
    assert results[0].rank == 1
    assert results[0].notes == ("Similarity is below expected threshold 0.500.",)


def test_format_similarity_example_results_returns_readable_lines() -> None:
    lines = format_similarity_example_results(
        [
            similarity_examples.SimilarityExampleResult(
                player="Target Player",
                expected_player="Expected Player",
                passed=True,
                rank=1,
                similarity=0.8,
                notes=("Expected player returned within threshold.",),
            )
        ]
    )

    assert lines == [
        "PASS | Target Player -> Expected Player | rank 1 | similarity 0.800",
        "  - Expected player returned within threshold.",
    ]
