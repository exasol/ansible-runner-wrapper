import importlib
import pathlib
import tempfile
import test.ansible
from collections import namedtuple
from collections.abc import Callable
from pathlib import Path
from typing import (
    Any,
    Iterable,
)
from unittest.mock import Mock

import pytest
import exasol.ansible as ansible

from exasol.ansible.access import Event
from exasol.ansible.context import FilenameConflict
from exasol.ansible.inventory import InventoryHost
from exasol.ansible.repository import default_repositories
from exasol.ansible.run_install_dependencies import run_install_dependencies
from exasol.ds.sandbox.lib.config import ConfigObject


class AnsibleTestAccess:

    def __init__(
        self, delegate: Callable[[str, ansible.Playbook], None] | None = None
    ):
        self.call_arguments = None
        self.arguments = namedtuple("Arguments", "private_data_dir playbook")
        self.delegate = delegate

    def run(
        self,
        private_data_dir: str,
        run_ctx: ansible.Playbook,
        event_handler: Callable[[Event], bool],
        event_logger: Callable[[str], None],
    ):
        self.call_arguments = self.arguments(private_data_dir, run_ctx)
        if self.delegate is not None:
            self.delegate(private_data_dir, run_ctx)


def _extra_vars(config):
    return {
        "ansible_runner_wrapper_version": config.ansible_runner_wrapper_version,
        "work_in_progress_notebooks": False,
    }


def _run_context(
    other: ansible.Playbook,
    extra_vars: dict[str, Any] | None = None,
) -> ansible.Playbook:
    return ansible.Playbook(file=other.file, vars=extra_vars or {})


def _run_context_from_config(
    other: ansible.Playbook,
    config: ConfigObject,
):
    extra_vars = {
        "ansible_runner_wrapper_version": config.ansible_runner_wrapper_version,
        "work_in_progress_notebooks": False,
    }
    return _run_context(other, extra_vars=extra_vars)


def test_run_ansible_default_values(test_config: ConfigObject):
    ansible_access = Mock(ansible.Access)
    run_context = ansible.Playbook(file="my_playbook.yml")
    run_install_dependencies(
        ansible_access,
        test_config,
        inventory_hosts=(),
        ansible_run_context=run_context,
    )
    actual_args = ansible_access.run.call_args.args
    assert actual_args[0].startswith(tempfile.gettempdir())
    assert actual_args[1] == _run_context_from_config(run_context, test_config)


def test_run_ansible_custom_playbook(test_config):
    """
    Test which executes run_install_dependencies with default ansible variable, but a custom playbook
    """
    ansible_access = AnsibleTestAccess()
    ansible_run_context = ansible.Playbook(file="my_playbook.yml")
    run_install_dependencies(
        ansible_access,
        test_config,
        inventory_hosts=(),
        ansible_run_context=ansible_run_context,
    )

    expected_ansible_run_context = ansible.Playbook(
        file="my_playbook.yml", vars=_extra_vars(test_config)
    )
    assert ansible_access.call_arguments.private_data_dir.startswith(
        tempfile.gettempdir()
    )
    assert ansible_access.call_arguments.playbook == expected_ansible_run_context


def test_run_ansible_custom_variables(test_config):
    """
    Test which executes run_install_dependencies with custam playbook and custom ansible variables
    """
    ansible_access = AnsibleTestAccess()
    ansible_run_context = ansible.Playbook(
        file="my_playbook.yml", vars={"my_var": True}
    )
    run_install_dependencies(
        ansible_access,
        test_config,
        inventory_hosts=(),
        ansible_run_context=ansible_run_context,
    )
    extra_vars = _extra_vars(test_config)
    extra_vars.update({"my_var": True})
    expected_ansible_run_context = ansible.Playbook(
        file="my_playbook.yml", vars=extra_vars
    )
    assert ansible_access.call_arguments.private_data_dir.startswith(
        tempfile.gettempdir()
    )
    assert ansible_access.call_arguments.playbook == expected_ansible_run_context


def test_run_ansible_check_inventory_empty_host(test_config):
    empty_inventory = "[test_targets]\n\n"

    def check_inventory(work_dir: str, ansible_run_context: ansible.Playbook):
        with open(
            f"{work_dir}/inventory",
        ) as f:
            inventory_content = f.read()
        assert inventory_content == empty_inventory

    run_install_dependencies(AnsibleTestAccess(check_inventory), test_config)


def test_run_ansible_check_inventory_custom_host(test_config):
    custom_inventory = (
        "[test_targets]\n\nmy_host ansible_ssh_private_key_file=my_key\n\n"
    )

    def check_inventory(work_dir: str, ansible_run_context: ansible.Playbook):
        with open(
            f"{work_dir}/inventory",
        ) as f:
            inventory_content = f.read()
        assert inventory_content == custom_inventory

    run_install_dependencies(
        AnsibleTestAccess(check_inventory),
        test_config,
        inventory_hosts=(InventoryHost("my_host", "my_key"),),
    )


def test_run_ansible_check_default_repository(test_config):
    """
    Test that default repository is being copied correctly.
    For simplicity, we check only if:
     1. the playbook of the default repository exists on target.
     2. One of the role files exists (Validate deep copy)
    """

    def check_playbook(work_dir: str, ansible_run_context: ansible.Playbook):
        p = pathlib.Path(work_dir) / "ansible_runner_wrapper_docker_playbook.yml"
        assert p.exists()
        p = pathlib.Path(work_dir) / "roles" / "jupyter" / "tasks" / "main.yml"
        assert p.exists()

    run_install_dependencies(AnsibleTestAccess(check_playbook), test_config)


def test_default_repository_enumerates_assets():
    assets = default_repositories[0].get_assets()
    relative_paths = sorted(str(asset.relative_path) for asset in assets)
    assert relative_paths == [
        "ansible_runner_wrapper_docker_playbook.yml",
        "general_setup_tasks.yml",
        "roles",
    ]


def test_repository_ignores_init_py_when_enumerating_assets():
    package = importlib.import_module("test.unit.resources.ignored_files")
    assets = ansible.ImportlibRepository(package).get_assets()
    relative_paths = [asset.relative_path for asset in assets]
    assert relative_paths == [Path("playbook.yml")]


def test_run_ansible_check_multiple_repositories(test_config):
    """
    Test that multiple repositories are being copied correctly.
    For simplicity, we check only if the playbook of the repositories exists on target.
    """

    def check_playbooks(work_dir: str, ansible_run_context: ansible.Playbook):
        p = pathlib.Path(f"{work_dir}/general_setup_tasks.yml")
        assert p.exists()
        p = pathlib.Path(f"{work_dir}/ansible_sample_playbook.yml")
        assert p.exists()

    test_repositories = default_repositories + (
        ansible.ImportlibRepository(test.ansible),
    )
    run_install_dependencies(
        AnsibleTestAccess(check_playbooks),
        test_config,
        inventory_hosts=(),
        ansible_run_context=ansible.Playbook(
            file="ansible_runner_wrapper_docker_playbook.yml"
        ),
        ansible_repositories=test_repositories,
    )


class Scenario:
    def __init__(self, playbook: str, package_names: list[str]):
        self.playbook = ansible.Playbook(file=playbook)
        self.package_names = package_names

    @property
    def _repositories(self) -> Iterable[ansible.Repository]:
        for name in self.package_names:
            package = importlib.import_module(name)
            yield ansible.ImportlibRepository(package)

    def run(self, context: ansible.Access = Mock(), path: Path | None = None):
        with ansible.Context(context, list(self._repositories), path) as runner:
            runner.run(self.playbook)


@pytest.mark.parametrize("module", ["lower_level", "top_level", "directory_vs_file"])
def test_filename_conflict(module):
    playbook = "ansible_runner_wrapper_docker_playbook.yml"
    modules = [
        "exasol.ds.sandbox.runtime.ansible",
        f"test.unit.resources.conflict.{module}",
    ]
    with pytest.raises(FilenameConflict):
        Scenario(playbook, modules).run()


def test_files_copied(tmp_path):
    Scenario("playbook.yml", ["test.unit.resources.simple"]).run(path=tmp_path)
    for f in ["playbook.yml", "roles/tasks/main.yml"]:
        assert (tmp_path / f).exists()
