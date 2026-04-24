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


@staticmethod
def _validate_assets(assets: tuple[AnsibleAsset, ...]) -> None:
    path_types: dict[Path, str] = {}
    for asset in assets:
        for occupied_path, path_type in asset.occupied_path_types().items():
            existing_type = path_types.get(occupied_path)
            if existing_type is not None:
                if existing_type == path_type == "file":
                    raise FilenameConflict(f"Duplicate file detected: {occupied_path}")
                raise FilenameConflict(f"Path collision detected: {occupied_path}")
            path_types[occupied_path] = path_type


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
    _validate_assets(assets)
    relative = Path(work_dir.name)
    for asset in assets:
        asset.copy_to(relative)

    yield AnsibleRunner(ansible_access, relative)

    work_dir.cleanup()
