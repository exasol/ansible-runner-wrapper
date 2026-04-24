from abc import abstractmethod
from pathlib import Path
from typing import Any

import exasol.ds.sandbox.runtime.ansible
from exasol.ds.sandbox.lib.logging import (
    LogType,
    get_status_logger,
)

try:
    import importlib.resources as ir
except ImportError:  # pragma: no cover
    import importlib_resources as ir  # type: ignore[no-redef]


LOG = get_status_logger(LogType.ANSIBLE)


def _should_ignore(path: Any) -> bool:
    if path.name in {"__init__.py", "__pycache__"}:
        LOG.debug(f"Ignoring {path} for repository.")
        return True
    return False


class AnsibleAsset:
    """
    Abstract representation of a copyable ansible asset within a repository.
    """

    def __init__(self, relative_path: Path):
        self.relative_path = relative_path

    @abstractmethod
    def copy_to(self, target_root: Path) -> None:
        """
        Copy this asset into the given target root.
        """
        raise NotImplementedError()

    def occupied_paths(self) -> set[Path]:
        """
        Return all relative paths this asset requires in the target tree.
        """
        raise NotImplementedError()

    def occupied_path_types(self) -> dict[Path, str]:
        """
        Return the required path types for this asset.
        """
        raise NotImplementedError()


class AnsibleRepository:
    """
    Abstract source of top-level ansible assets.
    """

    def get_assets(self) -> tuple[AnsibleAsset, ...]:
        """
        Base class does not implement asset enumeration.

        This method is intentionally left empty because:
        - Different repository types (e.g. filesystem-based, package-based)
          expose different asset sources.
        - Subclasses like `AnsibleResourceRepository` provide the actual
          implementation using their specific source (e.g. importlib resources).

        This class acts as an interface / abstraction layer.
        """
        raise NotImplementedError()


class ImportlibFileAsset(AnsibleAsset):

    def __init__(self, src_file: Any, relative_path: Path):
        super().__init__(relative_path)
        self._src_file = src_file

    def copy_to(self, target_root: Path) -> None:
        target_file = target_root / self.relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        content = self._src_file.read_bytes()
        with open(target_file, "wb") as file:
            file.write(content)

    def occupied_paths(self) -> set[Path]:
        return {self.relative_path}

    def occupied_path_types(self) -> dict[Path, str]:
        return {self.relative_path: "file"}


class ImportlibDirectoryAsset(AnsibleAsset):

    def __init__(self, src_path: Any, relative_path: Path):
        super().__init__(relative_path)
        self._src_path = src_path

    @classmethod
    def _copy_dir_tree(cls, src_path: Any, target_path: Path) -> None:
        if not target_path.exists():
            target_path.mkdir()
        for file in src_path.iterdir():
            if _should_ignore(file):
                continue
            file_target = target_path / file.name
            if file.is_file():
                content = file.read_bytes()
                with open(file_target, "wb") as target_file:
                    target_file.write(content)
            else:
                file_target.mkdir(exist_ok=True)
                cls._copy_dir_tree(file, file_target)

    @classmethod
    def _occupied_paths(cls, src_path: Any, relative_path: Path) -> set[Path]:
        occupied = {relative_path}
        for file in src_path.iterdir():
            if _should_ignore(file):
                continue
            child_relative_path = relative_path / file.name
            if file.is_file():
                occupied.add(child_relative_path)
            else:
                occupied.update(cls._occupied_paths(file, child_relative_path))
        return occupied

    def copy_to(self, target_root: Path) -> None:
        self._copy_dir_tree(self._src_path, target_root / self.relative_path)

    def occupied_paths(self) -> set[Path]:
        return self._occupied_paths(self._src_path, self.relative_path)

    @classmethod
    def _occupied_path_types(
        cls, src_path: Any, relative_path: Path
    ) -> dict[Path, str]:
        occupied = {relative_path: "directory"}
        for file in src_path.iterdir():
            if _should_ignore(file):
                continue
            child_relative_path = relative_path / file.name
            if file.is_file():
                occupied[child_relative_path] = "file"
            else:
                occupied.update(cls._occupied_path_types(file, child_relative_path))
        return occupied

    def occupied_path_types(self) -> dict[Path, str]:
        return self._occupied_path_types(self._src_path, self.relative_path)


class AnsibleResourceRepository(AnsibleRepository):
    """
    Represents a repository containing ansible files (roles, playbooks, tasks, etc.).
    The repository is expected to be located within a Python module.
    Supports copy of the ansible files to a target folder.
    """

    def __init__(self, package):
        self._package = package

    def get_assets(self) -> tuple[AnsibleAsset, ...]:
        """
        Enumerate the repository as top-level copyable assets.
        """
        source_path = ir.files(self._package)
        assets: list[AnsibleAsset] = []
        for file in source_path.iterdir():
            if _should_ignore(file):
                continue
            if file.is_file():
                assets.append(ImportlibFileAsset(file, Path(file.name)))
            else:
                assets.append(ImportlibDirectoryAsset(file, Path(file.name)))
        return tuple(assets)


default_repositories = (AnsibleResourceRepository(exasol.ds.sandbox.runtime.ansible),)
