from dataclasses import (
    dataclass,
    field,
)
from typing import Any


@dataclass
class Playbook:
    file: str
    vars: dict[str, Any] = field(default_factory=dict)
