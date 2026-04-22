from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Dict,
    Optional,
)


@dataclass
class AnsibleRunContext:
    playbook: str
    extra_vars: dict[str, Any] = field(default_factory=dict)


default_ansible_run_context = AnsibleRunContext(playbook="ec2_playbook.yml", extra_vars=None)
reset_password_ansible_run_context = AnsibleRunContext(playbook="reset_password.yml", extra_vars=None)
