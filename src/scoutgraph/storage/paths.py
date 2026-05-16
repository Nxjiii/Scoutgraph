from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved local folders used by the backend."""

    root: Path
    raw_data: Path
    processed_data: Path
    cache: Path

    @classmethod
    def from_root(cls, root: str | Path | None = None) -> "ProjectPaths":
        project_root = Path(root or ".").resolve()
        return cls(
            root=project_root,
            raw_data=project_root / "data" / "raw",
            processed_data=project_root / "data" / "processed",
            cache=project_root / "data" / "cache",
        )

    def ensure(self) -> None:
        """Create local data folders if they are missing."""
        self.raw_data.mkdir(parents=True, exist_ok=True)
        self.processed_data.mkdir(parents=True, exist_ok=True)
        self.cache.mkdir(parents=True, exist_ok=True)

