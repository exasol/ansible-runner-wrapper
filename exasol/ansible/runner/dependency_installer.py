from dataclasses import dataclass

from exasol.ansible.runner.ansible_repository import (
    AnsibleRepository, default_repositories)
from exasol.ansible.runner.ansible_run_context import (
    AnsibleRunContext, default_ansible_run_context)

from exasol.ansible.runner.ansible_access import AnsibleAccess

@dataclass
class AnsibleDependencyInstaller:
    ansible_access: AnsibleAccess
    run_context: AnsibleRunContext = default_ansible_run_context
    repositories: tuple[AnsibleRepository, ...] = default_repositories
