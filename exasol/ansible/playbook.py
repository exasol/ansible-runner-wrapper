from dataclasses import (
    dataclass,
    field,
)
from typing import Any


@dataclass
class Playbook:
    file: str
    vars: dict[str, Any] = field(default_factory=dict)


default_playbook = Playbook(file="ansible_runner_wrapper_docker_playbook.yml")
