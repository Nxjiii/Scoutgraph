from dataclasses import dataclass

import pandas as pd

from scoutgraph.similarity.player_similarity import find_similar_players
from scoutgraph.storage.paths import ProjectPaths


@dataclass(frozen=True)
class SimilarityExample:
    """A known player similarity expectation used as a sanity check."""

    player: str
    expected_player: str
    same_position: bool = True
    limit: int = 5
    minimum_similarity: float = 0.0


@dataclass(frozen=True)
class SimilarityExampleResult:
    """Result of running one known similarity example."""

    player: str
    expected_player: str
    passed: bool
    rank: int | None
    similarity: float | None
    notes: tuple[str, ...]


KNOWN_PLAYER_SIMILARITY_EXAMPLES = (
    SimilarityExample(
        player="Granit Xhaka",
        expected_player="Exequiel Alejandro Palacios",
        minimum_similarity=0.75,
    ),
    SimilarityExample(
        player="Jonathan Tah",
        expected_player="Edmond Fayçal Tapsoba",
        minimum_similarity=0.45,
    ),
    SimilarityExample(
        player="Mitchell Weiser",
        expected_player="Olivier Deman",
        minimum_similarity=0.3,
    ),
)


def run_known_similarity_examples(
    paths: ProjectPaths,
    examples: tuple[SimilarityExample, ...] = KNOWN_PLAYER_SIMILARITY_EXAMPLES,
) -> list[SimilarityExampleResult]:
    """Run known player similarity examples against the current feature matrix."""
    return [_run_example(paths, example) for example in examples]


def format_similarity_example_results(results: list[SimilarityExampleResult]) -> list[str]:
    lines = []
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        rank = result.rank if result.rank is not None else "not found"
        similarity = (
            f"{result.similarity:.3f}" if result.similarity is not None else "not available"
        )
        lines.append(
            f"{status} | {result.player} -> {result.expected_player} | "
            f"rank {rank} | similarity {similarity}"
        )
        lines.extend(f"  - {note}" for note in result.notes)
    return lines


def _run_example(paths: ProjectPaths, example: SimilarityExample) -> SimilarityExampleResult:
    players = find_similar_players(
        paths,
        player=example.player,
        limit=example.limit,
        same_position=example.same_position,
    )
    match = _find_result(players, example.expected_player)
    if match is None:
        return SimilarityExampleResult(
            player=example.player,
            expected_player=example.expected_player,
            passed=False,
            rank=None,
            similarity=None,
            notes=("Expected player was not returned in the configured result limit.",),
        )

    rank, row = match
    similarity = float(row["similarity"])
    notes = []
    if similarity < example.minimum_similarity:
        notes.append(
            f"Similarity is below expected threshold {example.minimum_similarity:.3f}."
        )
    if rank > 1:
        notes.append("Expected player was returned, but not as the top match.")
    if not notes:
        notes.append("Expected player returned within threshold.")

    return SimilarityExampleResult(
        player=example.player,
        expected_player=example.expected_player,
        passed=similarity >= example.minimum_similarity,
        rank=rank,
        similarity=similarity,
        notes=tuple(notes),
    )


def _find_result(players: pd.DataFrame, expected_player: str) -> tuple[int, pd.Series] | None:
    matches = players["player_name"].str.contains(expected_player, case=False, na=False)
    if not matches.any():
        return None
    index = int(players[matches].index[0])
    return index + 1, players.loc[index]
