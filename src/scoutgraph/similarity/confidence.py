from dataclasses import dataclass

import pandas as pd


LOW_MINUTES_THRESHOLD = 45
HIGH_SIMILARITY_THRESHOLD = 0.75
MEDIUM_SIMILARITY_THRESHOLD = 0.45


@dataclass(frozen=True)
class SimilarityConfidence:
    """Confidence and limitations for one similarity result."""

    level: str
    limitations: tuple[str, ...]


def evaluate_similarity_confidence(
    matrix: pd.DataFrame,
    *,
    player: str,
    compared_player: str,
    similarity: float,
    same_position: bool,
) -> SimilarityConfidence:
    """Evaluate how much trust to place in one similarity result."""
    target = _find_unique_player(matrix, player)
    compared = _find_unique_player(matrix, compared_player)
    limitations = [
        "match-level sample only",
        "based on the current generated feature matrix",
    ]

    if same_position:
        limitations.append("same broad-position filter applied")
    else:
        limitations.append("players may be from different broad position groups")

    if _minutes_played(target) < LOW_MINUTES_THRESHOLD:
        limitations.append(f"{target['player_name']} has fewer than {LOW_MINUTES_THRESHOLD} minutes")
    if _minutes_played(compared) < LOW_MINUTES_THRESHOLD:
        limitations.append(
            f"{compared['player_name']} has fewer than {LOW_MINUTES_THRESHOLD} minutes"
        )
    if similarity < MEDIUM_SIMILARITY_THRESHOLD:
        limitations.append("similarity score is below the medium-match threshold")
    elif similarity < HIGH_SIMILARITY_THRESHOLD:
        limitations.append("similarity score is moderate rather than strong")

    return SimilarityConfidence(
        level=_confidence_level(similarity=similarity, limitations=limitations),
        limitations=tuple(limitations),
    )


def format_similarity_confidence(confidence: SimilarityConfidence) -> list[str]:
    lines = [f"  Confidence: {confidence.level}", "  Limitations:"]
    lines.extend(f"  - {limitation}" for limitation in confidence.limitations)
    return lines


def _confidence_level(*, similarity: float, limitations: list[str]) -> str:
    has_low_minutes = any("fewer than" in limitation for limitation in limitations)
    if similarity >= HIGH_SIMILARITY_THRESHOLD and not has_low_minutes:
        return "high"
    if similarity >= MEDIUM_SIMILARITY_THRESHOLD:
        return "medium"
    return "low"


def _minutes_played(player: pd.Series) -> float:
    return float(player.get("minutes_played", 0))


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
