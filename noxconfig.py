from __future__ import annotations

from pathlib import Path

from exasol.toolbox.config import BaseConfig

PROJECT_CONFIG = BaseConfig(
    project_name="ansible",
    root_path=Path(__file__).parent,
    python_versions=("3.11", "3.12", "3.13", "3.14"),
)
