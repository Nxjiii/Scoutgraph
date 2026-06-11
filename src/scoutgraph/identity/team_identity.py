from dataclasses import dataclass

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


TEAM_FEATURE_MATRIX_PATH = "statsbomb/team_features.parquet"
HIGH_PERCENTILE_THRESHOLD = 75
TEAM_PERCENTILE_METRICS = [
    "passes_attempted",
    "pass_completion_pct",
    "progressive_passes",
    "carries",
    "progressive_carries",
    "shots",
    "xg",
]


@dataclass(frozen=True)
class TeamIdentity:
    """Readable tactical identity for one team feature vector."""

    team_name: str
    labels: tuple[str, ...]
    summary: str


def build_team_identity(paths: ProjectPaths, *, team: str) -> TeamIdentity:
    """Build tactical labels and a short summary for one team."""
    matrix = _load_team_features(paths)
    matrix = _add_team_percentiles(matrix)
    row = _find_unique_team(matrix, team)
    labels = _labels(row)
    return TeamIdentity(
        team_name=str(row["team_name"]),
        labels=tuple(labels),
        summary=_summary(row, labels),
    )


def format_team_identity(identity: TeamIdentity) -> list[str]:
    lines = [identity.team_name, "", "Labels:"]
    if identity.labels:
        lines.extend(f"- {label}" for label in identity.labels)
    else:
        lines.append("- balanced team profile")
    lines.extend(["", "Summary:", identity.summary])
    return lines


def _labels(row: pd.Series) -> list[str]:
    labels = []
    if _high_percentile(row, "passes_attempted"):
        labels.append("high-possession side")
    if _high_percentile(row, "pass_completion_pct"):
        labels.append("secure possession side")
    if _high_percentile(row, "progressive_passes"):
        labels.append("progressive passing side")
    if _high_percentile(row, "carries"):
        labels.append("active carrying side")
    if _high_percentile(row, "progressive_carries"):
        labels.append("progressive carrying side")
    if _high_percentile(row, "shots"):
        labels.append("high-shot side")
    if _high_percentile(row, "xg"):
        labels.append("strong shot creation side")
    return labels


def _summary(row: pd.Series, labels: list[str]) -> str:
    team_name = row["team_name"]
    if not labels:
        return f"{team_name} profiles as a balanced side in the current team sample."

    primary = _primary_style(labels)
    traits = _trait_phrase(labels, primary=primary)
    summary = f"{team_name} profiles as {primary} in the current team sample"
    if traits:
        summary = f"{summary}, with {traits}"
    return f"{summary}."


def _primary_style(labels: list[str]) -> str:
    if "high-possession side" in labels and "strong shot creation side" in labels:
        return "a possession-heavy attacking side"
    if "progressive passing side" in labels and "progressive carrying side" in labels:
        return "a direct ball-progression side"
    if "strong shot creation side" in labels:
        return "an attack-minded side"
    if "high-possession side" in labels:
        return "a possession-heavy side"
    if "progressive passing side" in labels:
        return "a progressive passing side"
    if "progressive carrying side" in labels:
        return "a progressive carrying side"
    if "high-shot side" in labels:
        return "a high-shot side"
    return "a balanced side"


def _trait_phrase(labels: list[str], *, primary: str) -> str:
    primary_labels = {
        "a progressive passing side": {"progressive passing side"},
        "a progressive carrying side": {"progressive carrying side"},
        "a high-shot side": {"high-shot side"},
    }.get(primary, set())
    trait_labels = [
        label
        for label in labels
        if label
        not in {"high-possession side", "strong shot creation side", *primary_labels}
    ]
    if not trait_labels:
        return ""
    if len(trait_labels) == 1:
        return trait_labels[0]
    return f"{', '.join(trait_labels[:-1])}, and {trait_labels[-1]}"


def _load_team_features(paths: ProjectPaths) -> pd.DataFrame:
    path = paths.processed_data / TEAM_FEATURE_MATRIX_PATH
    if not path.exists():
        raise FileNotFoundError(f"Team feature matrix not found: {path}. Build it first.")
    return pd.read_parquet(path)


def _add_team_percentiles(matrix: pd.DataFrame) -> pd.DataFrame:
    output = matrix.copy()
    for metric in TEAM_PERCENTILE_METRICS:
        if metric not in output.columns:
            continue
        output[f"{metric}_percentile"] = output[metric].rank(method="average", pct=True).mul(100)
    return output


def _high_percentile(row: pd.Series, metric: str) -> bool:
    percentile = row.get(f"{metric}_percentile")
    value = row.get(metric)
    return (
        pd.notna(percentile)
        and pd.notna(value)
        and value > 0
        and percentile >= HIGH_PERCENTILE_THRESHOLD
    )


def _find_unique_team(matrix: pd.DataFrame, team: str) -> pd.Series:
    matches = matrix[matrix["team_name"].str.contains(team, case=False, na=False)]
    if matches.empty:
        msg = f"No team found matching {team!r}."
        raise ValueError(msg)
    if len(matches) > 1:
        names = ", ".join(matches["team_name"].astype(str).tolist())
        msg = f"Multiple matches found for {team!r}: {names}. Use a more specific name."
        raise ValueError(msg)
    return matches.iloc[0]
