from pathlib import Path

from scoutgraph.storage.paths import ProjectPaths


def test_project_paths_resolve_from_root(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert paths.root == tmp_path
    assert paths.raw_data == tmp_path / "data" / "raw"
    assert paths.processed_data == tmp_path / "data" / "processed"
    assert paths.cache == tmp_path / "data" / "cache"


def test_project_paths_can_create_data_folders(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    paths.ensure()

    assert paths.raw_data.is_dir()
    assert paths.processed_data.is_dir()
    assert paths.cache.is_dir()

