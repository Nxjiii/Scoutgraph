from dataclasses import dataclass

import pandas as pd


EXPLANATION_METRICS = {
    "passes_attempted_per_90": "pass volume",
    "progressive_passes_per_90": "progressive passing",
    "carries_per_90": "carry volume",
    "progressive_carries_per_90": "progressive carrying",
    "shots_per_90": "shot volume",
    "xg_per_90": "shooting threat",
    "pass_completion_pct": "pass security",
}
SIMILARITY_RATIO_THRESHOLD = 0.15
DIFFERENCE_RATIO_THRESHOLD = 0.3


@dataclass(frozen=True)
class SimilarityExplanation:
    """Human-readable reasons for one player similarity result."""

    player_name: str
    compared_player_name: str
    shared_traits: tuple[str, ...]
    differences: tuple[str, ...]


def explain_player_similarity(
    matrix: pd.DataFrame,
    *,
    player: str,
    compared_player: str,
    max_items: int = 3,
) -> SimilarityExplanation:
    """Explain why two player feature vectors are close or different."""
    target = _find_unique_player(matrix, player)
    compared = _find_unique_player(matrix, compared_player)

    shared_traits = _shared_traits(target, compared, max_items=max_items)
    differences = _differences(target, compared, max_items=max_items)

    return SimilarityExplanation(
        player_name=str(target["player_name"]),
        compared_player_name=str(compared["player_name"]),
        shared_traits=tuple(shared_traits),
        differences=tuple(differences),
    )


def format_similarity_explanation(explanation: SimilarityExplanation) -> list[str]:
    lines = ["  Shared traits:"]
    if explanation.shared_traits:
        lines.extend(f"  - {trait}" for trait in explanation.shared_traits)
    else:
        lines.append("  - No close metric matches found.")

    lines.append("  Differences:")
    if explanation.differences:
        lines.extend(f"  - {difference}" for difference in explanation.differences)
    else:
        lines.append("  - No major metric differences found.")
    return lines


def _shared_traits(
    target: pd.Series,
    compared: pd.Series,
    *,
    max_items: int,
) -> list[str]:
    candidates = []
    for metric, label in EXPLANATION_METRICS.items():
        if metric not in target.index or metric not in compared.index:
            continue
        target_value = float(target[metric])
        compared_value = float(compared[metric])
        difference_ratio = _difference_ratio(target_value, compared_value)
        if difference_ratio <= SIMILARITY_RATIO_THRESHOLD:
            candidates.append((difference_ratio, label))

    candidates.sort(key=lambda candidate: candidate[0])
    return [f"similar {label}" for _, label in candidates[:max_items]]


def _differences(
    target: pd.Series,
    compared: pd.Series,
    *,
    max_items: int,
) -> list[str]:
    candidates = []
    for metric, label in EXPLANATION_METRICS.items():
        if metric not in target.index or metric not in compared.index:
            continue
        target_value = float(target[metric])
        compared_value = float(compared[metric])
        difference_ratio = _difference_ratio(target_value, compared_value)
        if difference_ratio >= DIFFERENCE_RATIO_THRESHOLD:
            candidates.append(
                (
                    difference_ratio,
                    _difference_text(target, compared, label, target_value, compared_value),
                )
            )

    candidates.sort(key=lambda candidate: candidate[0], reverse=True)
    return [text for _, text in candidates[:max_items]]


def _difference_text(
    target: pd.Series,
    compared: pd.Series,
    label: str,
    target_value: float,
    compared_value: float,
) -> str:
    if target_value > compared_value:
        return f"{target['player_name']} has higher {label}"
    return f"{compared['player_name']} has higher {label}"


def _difference_ratio(left: float, right: float) -> float:
    denominator = max(abs(left), abs(right), 0.01)
    return abs(left - right) / denominator


def _find_unique_player(matrix: pd.DataFrame, player: str) -> pd.Series:
    matches = matrix[matrix["player_name"].str.contains(player, case=False, na=False)]
    if matches.empty:
        msg = f"No player found matching {player!r}."
        raise ValueError(msg)
    if len(matches) > 1:
        names = ", ".join(matches["player_name"].astype(str).tolist())
        msg = f"Multiple matches found for {player!r}: {names}. Use a more specific name."
        raise ValueError(msg)
    return matches.iloc[0]
