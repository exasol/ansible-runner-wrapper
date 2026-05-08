import contextlib
import tempfile
from collections.abc import Generator
from pathlib import Path

from exasol.ansible.repository import (
    Asset,
    Repository,
)


class FilenameConflict(RuntimeError):
    """
    Signals duplicate filenames or files vs. directories when using
    multiple instances of Repository.
    """


class AssetCopier:
    def __init__(self, relative_target: Path):
        self.target = relative_target
        self._seen: dict[Path, str] = {}

    def copy(self, asset: Asset) -> None:
        for path, path_type in asset.paths().items():
            if (existing := self._seen.get(path)) is not None:
                if existing == path_type == "file":
                    raise FilenameConflict(f"Duplicate file detected: {path}")
                raise FilenameConflict(f"Path collision detected: {path}")
            self._seen[path] = path_type
        asset.copy_to(self.target)


@contextlib.contextmanager
def copy_files(
    repositories: list[Repository] | tuple[Repository, ...],
    work_dir: Path | None = None,
) -> Generator[Path]:
    with contextlib.ExitStack() as stack:
        if work_dir is None:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())
            work_dir = Path(temp_dir)
        copier = AssetCopier(work_dir)
        for repository in repositories:
            for asset in repository.get_assets():
                copier.copy(asset)
        yield work_dir
