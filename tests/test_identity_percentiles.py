import pandas as pd
import pytest

from scoutgraph.identity.percentiles import add_position_group_percentiles


def test_add_position_group_percentiles_ranks_metrics_within_position_groups() -> None:
    matrix = pd.DataFrame(
        [
            {"player_name": "Fullback A", "position_group": "defender", "shots_per_90": 1},
            {"player_name": "Fullback B", "position_group": "defender", "shots_per_90": 2},
            {"player_name": "Fullback C", "position_group": "defender", "shots_per_90": 3},
            {"player_name": "Fullback D", "position_group": "defender", "shots_per_90": 4},
            {"player_name": "Forward A", "position_group": "forward", "shots_per_90": 1},
            {"player_name": "Forward B", "position_group": "forward", "shots_per_90": 3},
            {"player_name": "Forward C", "position_group": "forward", "shots_per_90": 5},
            {"player_name": "Forward D", "position_group": "forward", "shots_per_90": 7},
        ]
    )

    scored = add_position_group_percentiles(matrix, metrics=["shots_per_90"])

    fullback = scored[scored["player_name"] == "Fullback C"].iloc[0]
    forward = scored[scored["player_name"] == "Forward B"].iloc[0]
    assert fullback["shots_per_90"] == forward["shots_per_90"] == 3
    assert fullback["shots_per_90_percentile"] == 75.0
    assert forward["shots_per_90_percentile"] == 50.0


def test_add_position_group_percentiles_requires_position_group() -> None:
    matrix = pd.DataFrame([{"player_name": "Example Player", "shots_per_90": 3}])

    with pytest.raises(ValueError, match="must include position_group"):
        add_position_group_percentiles(matrix, metrics=["shots_per_90"])
