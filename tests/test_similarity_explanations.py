import pandas as pd
import pytest

from scoutgraph.similarity.explanations import (
    explain_player_similarity,
    format_similarity_explanation,
)


def test_explain_player_similarity_returns_shared_traits_and_differences() -> None:
    matrix = pd.DataFrame(
        [
            {
                "player_name": "Granit Xhaka",
                "passes_attempted_per_90": 100,
                "progressive_passes_per_90": 22,
                "carries_per_90": 40,
                "shots_per_90": 3,
                "xg_per_90": 0.12,
                "pass_completion_pct": 91.0,
            },
            {
                "player_name": "Exequiel Palacios",
                "passes_attempted_per_90": 96,
                "progressive_passes_per_90": 10,
                "carries_per_90": 42,
                "shots_per_90": 1,
                "xg_per_90": 0.08,
                "pass_completion_pct": 90.0,
            },
        ]
    )

    explanation = explain_player_similarity(
        matrix,
        player="Xhaka",
        compared_player="Palacios",
    )

    assert explanation.shared_traits == (
        "similar pass security",
        "similar pass volume",
        "similar carry volume",
    )
    assert explanation.differences == (
        "Granit Xhaka has higher shot volume",
        "Granit Xhaka has higher progressive passing",
        "Granit Xhaka has higher shooting threat",
    )


def test_format_similarity_explanation_returns_readable_lines() -> None:
    explanation = explain_player_similarity(
        pd.DataFrame(
            [
                {
                    "player_name": "A",
                    "passes_attempted_per_90": 10,
                    "carries_per_90": 10,
                },
                {
                    "player_name": "B",
                    "passes_attempted_per_90": 10,
                    "carries_per_90": 20,
                },
            ]
        ),
        player="A",
        compared_player="B",
    )

    assert format_similarity_explanation(explanation) == [
        "  Shared traits:",
        "  - similar pass volume",
        "  Differences:",
        "  - B has higher carry volume",
    ]


def test_explain_player_similarity_rejects_ambiguous_player_name() -> None:
    matrix = pd.DataFrame(
        [
            {"player_name": "Alex One", "passes_attempted_per_90": 10},
            {"player_name": "Alex Two", "passes_attempted_per_90": 10},
            {"player_name": "Target", "passes_attempted_per_90": 10},
        ]
    )

    with pytest.raises(ValueError, match="Multiple matches found"):
        explain_player_similarity(matrix, player="Alex", compared_player="Target")
