import tempfile
from pathlib import Path
from typing import Tuple

from exasol.ansible.runner.ansible_access import AnsibleAccess
from exasol.ansible.runner.ansible_repository import AnsibleRepository
from exasol.ansible.runner.ansible_runner import AnsibleRunner


class AnsibleContextManager:
    """
    Context manager which creates a temporary working directory where ansible files are stored.
    During creation, the content of all given ansible repositories is copied to the temporary directory.
    Deletes the directory during cleanup.
    """

    def __init__(self, ansible_access: AnsibleAccess, repositories: Tuple[AnsibleRepository]):
        self._work_dir = None
        self._ansible_access = ansible_access
        self._ansible_repositories = repositories

    def __enter__(self):
        self._work_dir = tempfile.TemporaryDirectory()
        work_path = Path(self._work_dir.name)

        copied_files = set()

        for repo in self._ansible_repositories:
            for file_path in repo.path.rglob("*"):
                if file_path.is_file():

                    relative = file_path.relative_to(repo.path)
                    target = work_path / relative

                    # ❗ required by tests: detect duplicate files across repos
                    if target in copied_files or target.exists():
                        raise RuntimeError(f"Duplicate file in repositories: {relative}")

                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(file_path.read_bytes())

                    copied_files.add(target)

        return AnsibleRunner(self._ansible_access, work_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._work_dir.cleanup()