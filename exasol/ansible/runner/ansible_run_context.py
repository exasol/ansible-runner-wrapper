from dataclasses import (
    dataclass,
    field,
)
from typing import Any


@dataclass
class AnsibleRunContext:
    playbook: str
    extra_vars: dict[str, Any] = field(default_factory=dict)


default_ansible_run_context = AnsibleRunContext(
    playbook="ansible_runner_wrapper_docker_playbook.yml"
)
