from exasol.ansible.runner.ansible_access import AnsibleAccess
from exasol.ansible.runner.ansible_context_manager import ansible_context_manager
from exasol.ansible.runner.ansible_repository import (
    AnsibleRepository,
    default_repositories,
)
from exasol.ansible.runner.ansible_run_context import (
    AnsibleRunContext,
    default_ansible_run_context,
)
from exasol.ansible.runner.facts import AnsibleFacts
from exasol.ansible.runner.inventory import InventoryHost
from exasol.ds.sandbox.lib.config import ConfigObject


def run_install_dependencies(
    ansible_access: AnsibleAccess,
    configuration: ConfigObject,
    inventory_hosts: tuple[InventoryHost, ...] = (),
    ansible_run_context: AnsibleRunContext = default_ansible_run_context,
    ansible_repositories: tuple[AnsibleRepository, ...] = default_repositories,
) -> AnsibleFacts:
    """
    Run Ansible in a temporary working directory populated from the configured
    repositories and inventory hosts.
    """
    new_extra_vars = {
        "ansible_runner_wrapper_version": configuration.ansible_runner_wrapper_version,
        "work_in_progress_notebooks": False,
    }
    if ansible_run_context.extra_vars is not None:
        new_extra_vars.update(ansible_run_context.extra_vars)
    new_ansible_run_context = AnsibleRunContext(
        ansible_run_context.playbook, new_extra_vars
    )
    with ansible_context_manager(ansible_access, ansible_repositories) as ansible_runner:
        facts = ansible_runner.run(
            new_ansible_run_context,
            inventory_hosts=inventory_hosts,
        )
    return facts
