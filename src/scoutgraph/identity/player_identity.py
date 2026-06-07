from dataclasses import dataclass

import pandas as pd

from scoutgraph.identity.percentiles import add_position_group_percentiles
from scoutgraph.similarity.player_positions import load_player_position_groups
from scoutgraph.storage.paths import ProjectPaths


PLAYER_FEATURE_MATRIX_PATH = "statsbomb/player_features.parquet"
LOW_MINUTES_THRESHOLD = 45
# Top-quartile cutoff: label a trait when the player is high versus positional peers.
HIGH_PERCENTILE_THRESHOLD = 75


@dataclass(frozen=True)
class PlayerIdentity:
    """Readable tactical identity for one player feature vector."""

    player_name: str
    team_name: str
    position_group: str
    labels: tuple[str, ...]
    summary: str


def build_player_identity(paths: ProjectPaths, *, player: str) -> PlayerIdentity:
    """Build tactical labels and a short summary for one player."""
    matrix = _load_player_features(paths)
    matrix = _add_position_context(paths, matrix)
    matrix = add_position_group_percentiles(matrix)
    row = _find_unique_player(matrix, player)
    if pd.isna(row["position_group"]):
        msg = f"No position group found for {row['player_name']}. Normalize player positions first."
        raise ValueError(msg)
    labels = _labels(row)
    return PlayerIdentity(
        player_name=str(row["player_name"]),
        team_name=str(row["team_name"]),
        position_group=str(row["position_group"]),
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
    if _high_percentile(row, "passes_attempted_per_90"):
        labels.append("high-volume passer")
    if _high_percentile(row, "progressive_passes_per_90"):
        labels.append("progressive passer")
    if _high_percentile(row, "carries_per_90"):
        labels.append("active ball carrier")
    if _high_percentile(row, "progressive_carries_per_90"):
        labels.append("progressive ball carrier")
    if _high_percentile(row, "shots_per_90"):
        labels.append("frequent shooter")
    if _high_percentile(row, "xg_per_90"):
        labels.append("shooting threat")
    if _high_percentile(row, "pass_completion_pct"):
        labels.append("secure passer")
    return labels


def _summary(row: pd.Series, labels: list[str]) -> str:
    player_name = row["player_name"]
    if not labels:
        return f"{player_name} profiles as a balanced player in the current feature sample."

    primary = _primary_role(row, labels)
    traits = _trait_phrase(labels)
    summary = f"{player_name} profiles as {primary}"
    if traits:
        summary = f"{summary}, with {traits}"
    if "low-minute sample" in labels:
        summary = f"{summary}. Treat this profile cautiously because the sample is low-minute"
    return f"{summary}."


def _primary_role(row: pd.Series, labels: list[str]) -> str:
    if "shooting threat" in labels and row["position_group"] == "forward":
        return "a shooting-focused attacker"
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


def _add_position_context(paths: ProjectPaths, matrix: pd.DataFrame) -> pd.DataFrame:
    if "position_group" in matrix.columns:
        return matrix
    position_groups = load_player_position_groups(paths)
    return matrix.merge(position_groups, on=["player_id", "team_id"], how="left")


def _high_percentile(row: pd.Series, metric: str) -> bool:
    percentile = row.get(f"{metric}_percentile")
    return pd.notna(percentile) and percentile >= HIGH_PERCENTILE_THRESHOLD


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
