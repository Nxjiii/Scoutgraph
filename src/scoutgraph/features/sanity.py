from dataclasses import dataclass
from numbers import Number

import pandas as pd

from scoutgraph.storage.paths import ProjectPaths


IDENTITY_COLUMNS = {"player_id", "player_name", "team_id", "team_name"}


@dataclass(frozen=True)
class FeatureInspection:
    """Readable inspection result for one generated feature vector."""

    title: str
    metrics: tuple[tuple[str, float], ...]
    warnings: tuple[str, ...]


def inspect_player_vector(paths: ProjectPaths, *, player: str) -> FeatureInspection:
    """Inspect one uniquely matched player feature vector."""
    matrix = _read_matrix(paths, "player_features.parquet")
    row = _find_unique_row(matrix, column="player_name", query=player)
    title = f"{row['player_name']} | {row['team_name']}"
    warnings = _common_warnings(row)
    if row["minutes_played"] < 45:
        warnings.append("Low-minute sample: per-90 metrics may be unstable.")
    return FeatureInspection(title, _numeric_metrics(row), tuple(warnings))


def inspect_team_vector(paths: ProjectPaths, *, team: str) -> FeatureInspection:
    """Inspect one uniquely matched team feature vector."""
    matrix = _read_matrix(paths, "team_features.parquet")
    row = _find_unique_row(matrix, column="team_name", query=team)
    return FeatureInspection(
        str(row["team_name"]),
        _numeric_metrics(row),
        tuple(_common_warnings(row)),
    )


def format_feature_inspection(inspection: FeatureInspection) -> list[str]:
    """Format one feature inspection for terminal output."""
    lines = [inspection.title, "", "Metrics"]
    lines.extend(f"- {_display_name(name)}: {value}" for name, value in inspection.metrics)
    lines.extend(["", "Warnings"])
    if inspection.warnings:
        lines.extend(f"- {warning}" for warning in inspection.warnings)
    else:
        lines.append("- None")
    return lines


def _common_warnings(row: pd.Series) -> list[str]:
    warnings = []
    if row.isna().any():
        warnings.append("One or more feature values are missing.")
    if _value(row, "pass_completion_pct") > 100:
        warnings.append("Pass completion percentage is above 100.")
    if _value(row, "passes_completed") > _value(row, "passes_attempted"):
        warnings.append("Completed passes exceed attempted passes.")
    if _value(row, "goals") > _value(row, "shots"):
        warnings.append("Goals exceed shots.")
    if _value(row, "shots_on_target") > _value(row, "shots"):
        warnings.append("Shots on target exceed total shots.")
    numeric = row.drop(labels=[column for column in IDENTITY_COLUMNS if column in row.index])
    if any(value < 0 for value in numeric if isinstance(value, Number)):
        warnings.append("One or more feature values are negative.")
    return warnings


def _numeric_metrics(row: pd.Series) -> tuple[tuple[str, float], ...]:
    metrics = []
    for name, value in row.items():
        if name in IDENTITY_COLUMNS or not isinstance(value, Number):
            continue
        metrics.append((name, round(float(value), 3)))
    return tuple(metrics)


def _find_unique_row(matrix: pd.DataFrame, *, column: str, query: str) -> pd.Series:
    matches = matrix[matrix[column].str.contains(query, case=False, na=False)]
    if matches.empty:
        msg = f"No {column.replace('_name', '')} found matching {query!r}."
        raise ValueError(msg)
    if len(matches) > 1:
        names = ", ".join(matches[column].astype(str).tolist())
        msg = f"Multiple matches found for {query!r}: {names}. Use a more specific name."
        raise ValueError(msg)
    return matches.iloc[0]


def _read_matrix(paths: ProjectPaths, filename: str) -> pd.DataFrame:
    path = paths.processed_data / "statsbomb" / filename
    if not path.exists():
        raise FileNotFoundError(f"Feature matrix not found: {path}. Build it before inspecting.")
    return pd.read_parquet(path)


def _display_name(name: str) -> str:
    return name.replace("_", " ")


def _value(row: pd.Series, column: str) -> float:
    return float(row.get(column, 0))
