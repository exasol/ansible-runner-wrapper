from abc import abstractmethod
from collections.abc import Iterable
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
    if path.name in {"__init__.py", "__pycache__", ".DS_Store"}:
        LOG.debug(f"Ignoring {path} for repository.")
        return True
    return False


class Asset:
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
        ...

    @abstractmethod
    def paths(self) -> dict[Path, str]:
        """
        Return the contained paths for this asset.

        The string values in the dict are either "directory" or "file" to
        signal different types of assets.
        """
        ...


class ImportlibFileAsset(Asset):
    def __init__(self, src_file: Any, relative_path: Path):
        super().__init__(relative_path)
        self._src_file = src_file

    def copy_to(self, target_root: Path) -> None:
        target_file = target_root / self.relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        content = self._src_file.read_bytes()
        with open(target_file, "wb") as file:
            file.write(content)

    def paths(self) -> dict[Path, str]:
        return {self.relative_path: "file"}


class ImportlibDirectoryAsset(Asset):
    def __init__(self, src_path: Any, relative_path: Path):
        super().__init__(relative_path)
        self._src_path = src_path

    @classmethod
    def _paths(cls, src_path: Any, relative_path: Path) -> Iterable[tuple[Path, str]]:
        yield relative_path, "directory"
        for child in src_path.iterdir():
            if _should_ignore(child):
                continue
            child_path = relative_path / child.name
            if child.is_file():
                yield child_path, "file"
            else:
                yield from cls._paths(child, child_path)

    def copy_to(self, target_root: Path) -> None:
        for path, path_type in self._paths(self._src_path, self.relative_path):
            target = target_root / path
            if path_type == "file":
                target.parent.mkdir(parents=True, exist_ok=True)
                content = (self._src_path / path.relative_to(self.relative_path)).read_bytes()
                with open(target, "wb") as file:
                    file.write(content)
            else:
                target.mkdir(exist_ok=True)

    def paths(self) -> dict[Path, str]:
        return dict(self._paths(self._src_path, self.relative_path))


class Repository:
    """
    Abstract source of top-level ansible assets.
    """

    @abstractmethod
    def get_assets(self) -> Iterable[Asset]:
        """
        Base class does not implement asset enumeration.

        This method is intentionally left empty because:
        - Different repository types (e.g. filesystem-based, package-based)
          expose different asset sources.
        - Subclasses like `ImportlibRepository` provide the actual
          implementation using their specific source (e.g. importlib resources).

        This class acts as an interface / abstraction layer.
        """
        ...


class ImportlibRepository(Repository):
    """
    Represents a repository containing ansible files (roles, playbooks, tasks, etc.).
    The repository is expected to be located within a Python module.
    Supports copy of the ansible files to a target folder.
    """

    def __init__(self, package: Any):
        self._package = package

    def get_assets(self) -> Iterable[Asset]:
        """
        Traverse the repository and yield all copyable assets below it.
        """
        source_path = ir.files(self._package)
        for child in source_path.iterdir():
            if _should_ignore(child):
                continue
            if child.is_file():
                yield ImportlibFileAsset(child, Path(child.name))
            else:
                yield ImportlibDirectoryAsset(child, Path(child.name))


default_repositories = (ImportlibRepository(exasol.ds.sandbox.runtime.ansible),)
