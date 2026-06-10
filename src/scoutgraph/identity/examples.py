from dataclasses import dataclass

from scoutgraph.identity.player_identity import build_player_identity
from scoutgraph.storage.paths import ProjectPaths


@dataclass(frozen=True)
class IdentityExample:
    """A known player identity expectation used as a sanity check."""

    player: str
    expected_labels: tuple[str, ...]
    absent_labels: tuple[str, ...] = ()
    expected_summary_text: tuple[str, ...] = ()


@dataclass(frozen=True)
class IdentityExampleResult:
    """Result of running one known player identity example."""

    player: str
    passed: bool
    labels: tuple[str, ...]
    notes: tuple[str, ...]


KNOWN_PLAYER_IDENTITY_EXAMPLES = (
    IdentityExample(
        player="Granit Xhaka",
        expected_labels=("high-volume passer", "progressive passer", "active ball carrier"),
        absent_labels=("low-minute sample", "shooting threat"),
        expected_summary_text=("ball-progressing playmaker",),
    ),
    IdentityExample(
        player="Victor Okoh Boniface",
        expected_labels=("shooting threat", "frequent shooter"),
        absent_labels=("low-minute sample",),
        expected_summary_text=("shooting-focused attacker",),
    ),
    IdentityExample(
        player="Exequiel Alejandro Palacios",
        expected_labels=("low-minute sample",),
        expected_summary_text=("Treat this profile cautiously",),
    ),
)


def run_known_identity_examples(
    paths: ProjectPaths,
    examples: tuple[IdentityExample, ...] = KNOWN_PLAYER_IDENTITY_EXAMPLES,
) -> list[IdentityExampleResult]:
    """Run known player identity examples against the current feature matrix."""
    return [_run_example(paths, example) for example in examples]


def format_identity_example_results(results: list[IdentityExampleResult]) -> list[str]:
    lines = []
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        labels = ", ".join(result.labels) if result.labels else "balanced profile"
        lines.append(f"{status} | {result.player} | labels: {labels}")
        lines.extend(f"  - {note}" for note in result.notes)
    return lines


def _run_example(paths: ProjectPaths, example: IdentityExample) -> IdentityExampleResult:
    identity = build_player_identity(paths, player=example.player)
    labels = set(identity.labels)
    notes = [
        f"Missing expected label: {label}."
        for label in example.expected_labels
        if label not in labels
    ]
    notes.extend(
        f"Unexpected label present: {label}."
        for label in example.absent_labels
        if label in labels
    )
    notes.extend(
        f"Missing expected summary text: {text!r}."
        for text in example.expected_summary_text
        if text not in identity.summary
    )
    if not notes:
        notes.append("Expected identity traits were present.")

    return IdentityExampleResult(
        player=identity.player_name,
        passed=notes == ["Expected identity traits were present."],
        labels=identity.labels,
        notes=tuple(notes),
    )
