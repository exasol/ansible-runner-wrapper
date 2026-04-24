import tempfile
from contextlib import ExitStack
from pathlib import Path

from exasol.ansible.access import Access
from exasol.ansible.repository import (
    Asset,
    Repository,
)
from exasol.ansible.runner import Runner


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


class Context:
    """
    Create a temporary Ansible execution context from the given repositories.

    Args:
        ansible_access: Access configuration used by the created
            ``Runner``.
        repositories: Repositories whose assets are copied into the temporary
            execution directory.
        work_dir: Optional working directory to use instead of creating a new
            temporary directory.
    """

    def __init__(
        self,
        ansible_access: Access,
        repositories: list[Repository] | tuple[Repository, ...],
        work_dir: Path | None = None,
    ):
        self._ansible_access = ansible_access
        self._repositories = tuple(repositories)
        self._work_dir = work_dir
        self._stack: ExitStack | None = None

    def __enter__(self) -> Runner:
        stack = ExitStack()
        self._stack = stack
        work_dir = self._work_dir
        if work_dir is None:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())
            work_dir = Path(temp_dir)

        copier = AssetCopier(work_dir)
        for repository in self._repositories:
            for asset in repository.get_assets():
                copier.copy(asset)

        return Runner(self._ansible_access, work_dir)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._stack is not None:
            self._stack.close()
            self._stack = None
