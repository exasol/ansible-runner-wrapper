import contextlib
import tempfile
from pathlib import Path

from exasol.ansible.runner.ansible_access import AnsibleAccess
from exasol.ansible.runner.ansible_repository import (
    AnsibleAsset,
    AnsibleRepository,
)
from exasol.ansible.runner.ansible_runner import AnsibleRunner


class FilenameConflict(RuntimeError):
    """
    Signals duplicate filenames or files vs. directories when using
    multiple instances of AnsibleRepository.
    """


class AssetCopier:
    def __init__(self, relative_target: Path):
        self.target = relative_target
        self._seen: dict[Path, str] = {}

    def copy(self, asset: AnsibleAsset) -> None:
        for path, ptype in asset.paths().items():
            if (existing := self._seen.get(path)) is not None:
                if existing == ptype == "file":
                    raise FilenameConflict(f"Duplicate file detected: {path}")
                raise FilenameConflict(f"Path collision detected: {path}")
            self._seen[path] = ptype
        asset.copy_to(self.target)


@contextlib.contextmanager
def ansible_context_manager(
    ansible_access: AnsibleAccess,
    repositories: tuple[AnsibleRepository],
    work_dir: Path | None = None,
):
    """
    Create a temporary Ansible execution context from the given repositories.

    Args:
        ansible_access: Access configuration used by the created
            ``AnsibleRunner``.
        repositories: Repositories whose assets are copied into the temporary
            execution directory.
        work_dir: Optional working directory to use instead of creating a new
            temporary directory.
    """
    work_dir = work_dir or tempfile.TemporaryDirectory()
    assets = tuple(asset for repo in repositories for asset in repo.get_assets())
    relative = Path(work_dir.name)
    copier = AssetCopier(relative)
    for repo in repositories:
        for asset in repo.get_assets():
            copier.copy(asset)

    yield AnsibleRunner(ansible_access, relative)

    work_dir.cleanup()
