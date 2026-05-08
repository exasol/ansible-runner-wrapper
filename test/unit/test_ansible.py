import importlib
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

import exasol.ansible as ansible
from exasol.ansible import inventory
from exasol.ansible.context import FilenameConflict


def importlib_repository(package_name: str) -> ansible.Repository:
    package = importlib.import_module(package_name)
    return ansible.ImportlibRepository(package)


class Scenario:
    def __init__(
        self,
        playbook: ansible.Playbook,
        repositories: tuple[ansible.Repository, ...],
    ):
        self.playbook = playbook
        self.repositories = repositories

    def run(
        self,
        ansible_access: ansible.Access = Mock(),
        hosts: tuple[inventory.Host, ...] = (),
        path: Path | None = None,
    ):
        with ansible.Context(ansible_access, self.repositories, path) as runner:
            runner.run(self.playbook, hosts=hosts)


@pytest.fixture
def simple_scenario() -> Scenario:
    extra_vars = {"a": "aaa", "b": "bbb"}
    playbook = ansible.Playbook("playbook.yml", vars=extra_vars)
    repositories = (importlib_repository("test.resources.utest.simple"),)
    return Scenario(playbook, repositories)


def test_run_ansible_calls_ansible_access(simple_scenario):
    mock = Mock()
    simple_scenario.run(ansible_access=mock)
    args = mock.run.call_args.args
    assert args[0].startswith(tempfile.gettempdir())
    assert args[1] == simple_scenario.playbook
    assert not Path(args[0]).exists()


def test_files_copied(simple_scenario, tmp_path):
    simple_scenario.run(path=tmp_path)
    for f in ["playbook.yml", "roles/tasks/main.yml"]:
        assert (tmp_path / f).exists()


def test_importlib_resources_available_for_repository():
    import exasol.ansible.repository as repository

    package = importlib.import_module("test.resources.utest.simple")
    source_path = importlib.resources.files(package)

    assert source_path.joinpath("playbook.yml").is_file()


@pytest.mark.parametrize(
    "hosts, expected",
    [
        pytest.param(None, "[arw_inventory]\n\n", id="no_host"),
        pytest.param(
            (inventory.Host("HHH", Path("/tmp/K.pem")),),
            ("[arw_inventory]\n\n" "HHH ansible_ssh_private_key_file=/tmp/K.pem\n\n"),
            id="custom_host",
        ),
    ],
)
def test_inventory(simple_scenario, tmp_path, hosts, expected):
    simple_scenario.run(hosts=hosts, path=tmp_path)
    actual = (tmp_path / "inventory").read_text()
    assert actual == expected


def test_multi_playbook_assets():
    repo = importlib_repository("test.resources.utest.multiple-playbooks")
    actual = sorted(str(asset.relative_path) for asset in repo.get_assets())
    assert actual == ["p1.yml", "p2.yml", "p3.yml"]


def test_repository_ignores_init_py():
    repo = importlib_repository("test.resources.utest.ignored_files")
    actual = [asset.relative_path for asset in repo.get_assets()]
    assert actual == [Path("playbook.yml")]


@pytest.mark.parametrize("module", ["lower_level", "top_level", "directory_vs_file"])
def test_filename_conflicts(module):
    playbook = ansible.Playbook("playbook.yml")
    modules = [
        "test.resources.utest.simple",
        f"test.resources.utest.conflict.{module}",
    ]
    repos = tuple(importlib_repository(p) for p in modules)
    with pytest.raises(FilenameConflict):
        Scenario(playbook, repos).run()
