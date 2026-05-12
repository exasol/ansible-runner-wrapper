import importlib
import json
from pathlib import Path
from unittest.mock import (
    Mock,
)

import pytest

import exasol.ansible as ansible
from exasol.ansible import inventory
from exasol.ansible.context import FilenameConflict
from exasol.ansible.runner import ansible_runner


class Scenario:
    def __init__(
        self,
        playbook: ansible.Playbook,
        repositories: tuple[ansible.Repository, ...],
        path: Path,
        runner: Mock | None = None,
    ):
        self.playbook = playbook
        self.repositories = repositories
        self.path = path
        self.runner = runner or Mock()

    def run(
        self,
        hosts: tuple[inventory.Host, ...] = (),
    ):
        runner = ansible.Runner(self.repositories, self.path)
        runner.run(self.playbook, hosts=hosts)


@pytest.fixture
def mock_ansible_runner(monkeypatch):
    result = Mock(events=[], rc=0)
    mock = Mock(return_value=result)
    monkeypatch.setattr(ansible_runner, "run", mock)
    return mock


@pytest.fixture
def simple_scenario(tmp_path, mock_ansible_runner) -> Scenario:
    extravars = {"a": "aaa", "b": "bbb"}
    playbook = ansible.Playbook("playbook.yml", vars=extravars)
    repositories = (ansible.ImportlibRepository("test.resources.simple"),)
    return Scenario(playbook, repositories, tmp_path, mock_ansible_runner)


@pytest.fixture
def simple_repository() -> ansible.Repository:
    return ansible.ImportlibRepository("test.resources.simple")


def test_run_ansible_calls_ansible_runner(simple_scenario):
    simple_scenario.run()
    actual = simple_scenario.runner.call_args.kwargs
    assert actual["private_data_dir"] == str(simple_scenario.path)
    assert actual["playbook"] == "playbook.yml"
    assert actual["extravars"] == {"a": "aaa", "b": "bbb"}


def test_run_returns_legacy_fact_cache(
    tmp_path, mock_ansible_runner, simple_repository
):
    raw_facts = {"my_facts": {"sample_fact": "value"}}
    mock_ansible_runner.return_value.get_fact_cache.return_value = raw_facts

    runner = ansible.Runner((simple_repository,), tmp_path)
    actual = runner.run(ansible.Playbook("playbook.yml"), retrieve_facts_from="HHH")

    assert actual == raw_facts


def test_run_returns_ansible_2_19_prefixed_fact_cache(
    tmp_path,
    mock_ansible_runner,
    simple_repository,
):
    cache_dir = tmp_path / "artifacts" / "run" / "fact_cache"
    cache_dir.mkdir(parents=True)
    payload = {
        "my_facts": {
            "value": {
                "sample_fact": {
                    "value": "value",
                    "tags": [{"__ansible_type": "TrustedAsTemplate"}],
                    "__ansible_type": "_AnsibleTaggedStr",
                },
            },
            "tags": [{"__ansible_type": "Origin"}],
            "__ansible_type": "_AnsibleTaggedDict",
        },
    }
    (cache_dir / "s1_HHH").write_text(json.dumps({"__payload__": json.dumps(payload)}))
    result = mock_ansible_runner.return_value
    result.get_fact_cache.return_value = {}
    result.config.fact_cache = str(cache_dir)

    runner = ansible.Runner((simple_repository,), tmp_path)
    actual = runner.run(ansible.Playbook("playbook.yml"), retrieve_facts_from="HHH")

    assert actual == {"my_facts": {"sample_fact": "value"}}


def test_files_copied(simple_scenario):
    simple_scenario.run()
    for f in ["playbook.yml", "roles/tasks/main.yml"]:
        assert (simple_scenario.path / f).exists()


def test_importlib_resources_available_for_repository():
    package = importlib.import_module("test.resources.simple")
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
def test_inventory(simple_scenario, hosts, expected):
    simple_scenario.run(hosts=hosts)
    actual = (simple_scenario.path / "inventory").read_text()
    assert actual == expected


def test_multi_playbook_assets():
    repo = ansible.ImportlibRepository("test.resources.multiple-playbooks")
    actual = sorted(str(asset.relative_path) for asset in repo.get_assets())
    assert actual == ["p1.yml", "p2.yml", "p3.yml"]


def test_repository_ignores_init_py():
    repo = ansible.ImportlibRepository("test.resources.ignored_files")
    actual = [asset.relative_path for asset in repo.get_assets()]
    assert actual == [Path("playbook.yml")]


@pytest.mark.parametrize("module", ["lower_level", "top_level", "directory_vs_file"])
def test_filename_conflicts(module, tmp_path):
    playbook = ansible.Playbook("playbook.yml")
    modules = [
        "test.resources.simple",
        f"test.resources.conflict.{module}",
    ]
    repos = tuple(ansible.ImportlibRepository(p) for p in modules)
    with pytest.raises(FilenameConflict):
        Scenario(playbook, repos, tmp_path).run()
