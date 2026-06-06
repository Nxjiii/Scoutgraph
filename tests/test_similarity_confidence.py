import pandas as pd

from scoutgraph.similarity.confidence import (
    evaluate_similarity_confidence,
    format_similarity_confidence,
)


def test_evaluate_similarity_confidence_returns_high_for_strong_clean_match() -> None:
    confidence = evaluate_similarity_confidence(
        _matrix(),
        player="Xhaka",
        compared_player="Palacios",
        similarity=0.82,
        same_position=True,
    )

    assert confidence.level == "high"
    assert confidence.limitations == (
        "match-level sample only",
        "based on the current generated feature matrix",
        "same broad-position filter applied",
    )


def test_evaluate_similarity_confidence_flags_moderate_similarity() -> None:
    confidence = evaluate_similarity_confidence(
        _matrix(),
        player="Xhaka",
        compared_player="Palacios",
        similarity=0.62,
        same_position=True,
    )

    assert confidence.level == "medium"
    assert "similarity score is moderate rather than strong" in confidence.limitations


def test_evaluate_similarity_confidence_flags_low_minutes_and_low_similarity() -> None:
    confidence = evaluate_similarity_confidence(
        _matrix(minutes_played=25),
        player="Xhaka",
        compared_player="Palacios",
        similarity=0.31,
        same_position=False,
    )

    assert confidence.level == "low"
    assert "players may be from different broad position groups" in confidence.limitations
    assert "Palacios has fewer than 45 minutes" in confidence.limitations
    assert "similarity score is below the medium-match threshold" in confidence.limitations


def test_format_similarity_confidence_returns_readable_lines() -> None:
    confidence = evaluate_similarity_confidence(
        _matrix(),
        player="Xhaka",
        compared_player="Palacios",
        similarity=0.62,
        same_position=True,
    )

    assert format_similarity_confidence(confidence) == [
        "  Confidence: medium",
        "  Limitations:",
        "  - match-level sample only",
        "  - based on the current generated feature matrix",
        "  - same broad-position filter applied",
        "  - similarity score is moderate rather than strong",
    ]


def _matrix(*, minutes_played: float = 90) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_name": "Xhaka",
                "minutes_played": 90,
            },
            {
                "player_name": "Palacios",
                "minutes_played": minutes_played,
            },
        ]
    )
