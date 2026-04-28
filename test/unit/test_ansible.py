import importlib
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

import exasol.ansible as ansible
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
        path: Path | None = None,
    ):
        with ansible.Context(ansible_access, self.repositories, path) as runner:
            runner.run(self.playbook)


@pytest.fixture
def simple_scenario() -> Scenario:
    extra_vars = {"a": "aaa", "b": "bbb"}
    playbook = ansible.Playbook("playbook.yml", vars=extra_vars)
    repositories = (importlib_repository("test.unit.resources.simple"),)
    return Scenario(playbook, repositories)


def test_run_ansible_calls_ansible_access(simple_scenario):
    mock = Mock()
    simple_scenario.run(ansible_access=mock)
    args = mock.run.call_args.args
    assert args[0].startswith(tempfile.gettempdir())
    assert args[1] == simple_scenario.playbook


def test_files_copied(simple_scenario, tmp_path):
    simple_scenario.run(path=tmp_path)
    for f in ["playbook.yml", "roles/tasks/main.yml"]:
        assert (tmp_path / f).exists()


def test_multi_playbook_assets():
    repo = importlib_repository("test.unit.resources.multiple-playbooks")
    actual = sorted(str(asset.relative_path) for asset in repo.get_assets())
    assert actual == ["p1.yml", "p2.yml", "p3.yml"]


def test_repository_ignores_init_py():
    repo = importlib_repository("test.unit.resources.ignored_files")
    actual = [asset.relative_path for asset in repo.get_assets()]
    assert actual == [Path("playbook.yml")]


@pytest.mark.parametrize("module", ["lower_level", "top_level", "directory_vs_file"])
def test_filename_conflicts(module):
    playbook = ansible.Playbook("playbook.yml")
    modules = [
        "test.unit.resources.simple",
        f"test.unit.resources.conflict.{module}",
    ]
    repos = tuple((importlib_repository(p) for p in modules))
    with pytest.raises(FilenameConflict):
        Scenario(playbook, repos).run()
