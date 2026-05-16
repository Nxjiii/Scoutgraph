from typing import Protocol


class FootballDataSource(Protocol):
    """Small contract every source adapter should satisfy."""

    name: str

    def describe(self) -> str:
        """Return a human-readable description of what this source provides."""
        ...

