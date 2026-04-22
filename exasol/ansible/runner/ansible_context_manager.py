import tempfile
from pathlib import Path
from typing import Tuple

from exasol.ansible.runner.ansible_access import AnsibleAccess
from exasol.ansible.runner.ansible_repository import AnsibleRepository
from exasol.ansible.runner.ansible_runner import AnsibleRunner


class AnsibleContextManager:

    def __init__(self, ansible_access: AnsibleAccess, repositories: Tuple[AnsibleRepository]):
        self._work_dir = None
        self._ansible_access = ansible_access
        self._ansible_repositories = repositories

    def __enter__(self):
        self._work_dir = tempfile.TemporaryDirectory()
        work_path = Path(self._work_dir.name)

        seen_files = set()

        for repo in self._ansible_repositories:

            # capture state BEFORE copy
            before = set(work_path.rglob("*"))

            repo.copy_to(work_path)

            # compute only what was introduced by this repo
            after = set(work_path.rglob("*"))
            new_files = after - before

            for file_path in new_files:
                if file_path.is_file():
                    relative = file_path.relative_to(work_path)

                    if relative in seen_files:
                        raise RuntimeError(f"Duplicate file detected: {relative}")

                    seen_files.add(relative)

        return AnsibleRunner(self._ansible_access, work_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._work_dir.cleanup()