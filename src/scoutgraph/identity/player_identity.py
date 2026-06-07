from dataclasses import dataclass

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


PLAYER_FEATURE_MATRIX_PATH = "statsbomb/player_features.parquet"
LOW_MINUTES_THRESHOLD = 45


@dataclass(frozen=True)
class PlayerIdentity:
    """Readable tactical identity for one player feature vector."""

    player_name: str
    team_name: str
    labels: tuple[str, ...]
    summary: str


def build_player_identity(paths: ProjectPaths, *, player: str) -> PlayerIdentity:
    """Build tactical labels and a short summary for one player."""
    matrix = _load_player_features(paths)
    row = _find_unique_player(matrix, player)
    labels = _labels(row)
    return PlayerIdentity(
        player_name=str(row["player_name"]),
        team_name=str(row["team_name"]),
        labels=tuple(labels),
        summary=_summary(row, labels),
    )


def format_player_identity(identity: PlayerIdentity) -> list[str]:
    lines = [f"{identity.player_name} | {identity.team_name}", "", "Labels:"]
    if identity.labels:
        lines.extend(f"- {label}" for label in identity.labels)
    else:
        lines.append("- balanced profile")
    lines.extend(["", "Summary:", identity.summary])
    return lines


def _labels(row: pd.Series) -> list[str]:
    labels = []
    if row["minutes_played"] < LOW_MINUTES_THRESHOLD:
        labels.append("low-minute sample")
    if row["passes_attempted_per_90"] >= 75:
        labels.append("high-volume passer")
    if row["progressive_passes_per_90"] >= 18:
        labels.append("progressive passer")
    if row["carries_per_90"] >= 60:
        labels.append("active ball carrier")
    if row["progressive_carries_per_90"] >= 8:
        labels.append("progressive ball carrier")
    if row["shots_per_90"] >= 3:
        labels.append("frequent shooter")
    if row["xg_per_90"] >= 0.35:
        labels.append("shooting threat")
    if row["pass_completion_pct"] >= 90:
        labels.append("secure passer")
    return labels


def _summary(row: pd.Series, labels: list[str]) -> str:
    player_name = row["player_name"]
    if not labels:
        return f"{player_name} profiles as a balanced player in the current feature sample."

    primary = _primary_role(labels)
    traits = _trait_phrase(labels)
    summary = f"{player_name} profiles as {primary}"
    if traits:
        summary = f"{summary}, with {traits}"
    if "low-minute sample" in labels:
        summary = f"{summary}. Treat this profile cautiously because the sample is low-minute"
    return f"{summary}."


def _primary_role(labels: list[str]) -> str:
    if "shooting threat" in labels and "high-volume passer" not in labels:
        return "a shooting-focused attacker"
    if "progressive passer" in labels and "active ball carrier" in labels:
        return "a ball-progressing playmaker"
    if "high-volume passer" in labels:
        return "a high-volume passing hub"
    if "active ball carrier" in labels:
        return "an active ball carrier"
    return "a balanced player"


def _trait_phrase(labels: list[str]) -> str:
    trait_labels = [
        label
        for label in labels
        if label not in {"low-minute sample", "high-volume passer", "shooting threat"}
    ]
    if not trait_labels:
        return ""
    if len(trait_labels) == 1:
        return trait_labels[0]
    return f"{', '.join(trait_labels[:-1])}, and {trait_labels[-1]}"


def _load_player_features(paths: ProjectPaths) -> pd.DataFrame:
    path = paths.processed_data / PLAYER_FEATURE_MATRIX_PATH
    if not path.exists():
        raise FileNotFoundError(f"Player feature matrix not found: {path}. Build it first.")
    return pd.read_parquet(path)


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
