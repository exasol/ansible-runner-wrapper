from exasol import ansible
from exasol.ansible.inventory import InventoryHost
from exasol.ansible.playbook import default_playbook
from exasol.ansible.repository import default_repositories
from exasol.ds.sandbox.lib.config import ConfigObject


def run_install_dependencies(
    ansible_access: ansible.Access,
    configuration: ConfigObject,
    inventory_hosts: tuple[InventoryHost, ...] = (),
    ansible_run_context: ansible.Playbook = default_playbook,
    ansible_repositories: tuple[ansible.Repository, ...] = default_repositories,
) -> ansible.Facts:
    """
    Run Ansible in a temporary working directory populated from the configured
    repositories and inventory hosts.
    """
    vars_ = {
        "ansible_runner_wrapper_version": configuration.ansible_runner_wrapper_version,
        "work_in_progress_notebooks": False,
    }
    vars_.update(ansible_run_context.vars)
    playbook = ansible.Playbook(ansible_run_context.file, vars_)
    with ansible.Context(ansible_access, list(ansible_repositories)) as runner:
        return runner.run(playbook, inventory_hosts)
