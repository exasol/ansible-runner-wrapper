import tempfile
from pathlib import Path

from exasol.ansible.runner.ansible_access import AnsibleAccess
from exasol.ansible.runner.ansible_repository import (
    AnsibleAsset,
    AnsibleRepository,
)
from exasol.ansible.runner.ansible_runner import AnsibleRunner


class AnsibleContextManager:

    def __init__(
        self, ansible_access: AnsibleAccess, repositories: tuple[AnsibleRepository]
    ):
        self._work_dir = None
        self._ansible_access = ansible_access
        self._ansible_repositories = repositories

    @staticmethod
    def _validate_assets(assets: tuple[AnsibleAsset, ...]) -> None:
        path_types: dict[Path, str] = {}
        for asset in assets:
            for occupied_path, path_type in asset.occupied_path_types().items():
                existing_type = path_types.get(occupied_path)
                if existing_type is not None:
                    if existing_type == path_type == "file":
                        raise RuntimeError(f"Duplicate file detected: {occupied_path}")
                    raise RuntimeError(f"Path collision detected: {occupied_path}")
                path_types[occupied_path] = path_type

    def __enter__(self):
        self._work_dir = tempfile.TemporaryDirectory()
        work_path = Path(self._work_dir.name)

        assets = tuple(
            asset
            for repo in self._ansible_repositories
            for asset in repo.get_assets()
        )
        self._validate_assets(assets)
        for asset in assets:
            asset.copy_to(work_path)

        return AnsibleRunner(self._ansible_access, work_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._work_dir.cleanup()
