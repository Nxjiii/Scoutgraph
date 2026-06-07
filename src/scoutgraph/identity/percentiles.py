import pandas as pd


PERCENTILE_METRICS = [
    "passes_attempted_per_90",
    "progressive_passes_per_90",
    "carries_per_90",
    "progressive_carries_per_90",
    "shots_per_90",
    "xg_per_90",
    "pass_completion_pct",
]
POSITION_GROUP_COLUMN = "position_group"


def add_position_group_percentiles(
    matrix: pd.DataFrame,
    *,
    metrics: list[str] | None = None,
) -> pd.DataFrame:
    """Add percentile columns for each metric within broad position groups."""
    if POSITION_GROUP_COLUMN not in matrix.columns:
        msg = "Player feature matrix must include position_group before percentile scoring."
        raise ValueError(msg)

    output = matrix.copy()
    for metric in metrics or PERCENTILE_METRICS:
        if metric not in output.columns:
            continue
        output[f"{metric}_percentile"] = (
            output.groupby(POSITION_GROUP_COLUMN)[metric]
            .rank(method="average", pct=True)
            .mul(100)
            .round(1)
        )
    return output
