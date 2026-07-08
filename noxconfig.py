from __future__ import annotations

from pathlib import Path

from pydantic import computed_field

from exasol.toolbox.config import BaseConfig


class ProjectConfig(BaseConfig):
    @computed_field  # type: ignore[misc]
    @property
    def source_code_path(self) -> Path:
        return self.root_path / "exasol" / "ansible"


PROJECT_CONFIG = ProjectConfig(
    project_name="ansible-runner-wrapper",
    root_path=Path(__file__).parent,
    python_versions=("3.12", "3.13", "3.14"),
)
