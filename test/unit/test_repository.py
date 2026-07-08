from pathlib import Path

from exasol.ansible.repository import ImportlibDirectoryAsset


def test_directory_asset_paths_ignore_nested_metadata_files(tmp_path: Path) -> None:
    src_dir = tmp_path / "role"
    nested_dir = src_dir / "tasks"
    nested_dir.mkdir(parents=True)
    (nested_dir / "main.yml").write_text("- debug:\n")
    (nested_dir / "__init__.py").write_text("")
    (nested_dir / ".DS_Store").write_text("")
    (src_dir / "__pycache__").mkdir()

    asset = ImportlibDirectoryAsset(src_dir, Path("role"))

    actual = asset.paths()

    assert actual == {
        Path("role"): "directory",
        Path("role/tasks"): "directory",
        Path("role/tasks/main.yml"): "file",
    }
