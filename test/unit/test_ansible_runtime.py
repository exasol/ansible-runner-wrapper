import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch

from exasol import ansible
from exasol.ansible.access import (
    Access,
    AnsibleException,
    Event,
)
from exasol.ansible.facts import Facts
from exasol.ansible.repository import ImportlibDirectoryAsset
from exasol.ansible.runner import Runner


class FakeRunnerResult:
    def __init__(
        self,
        rc: int = 0,
        events: list[dict] | None = None,
        fact_cache: dict | None = None,
    ):
        self.rc = rc
        self.events = events or []
        self._fact_cache = fact_cache or {}

    def get_fact_cache(self, host: str) -> dict:
        return self._fact_cache[host]


def _install_fake_ansible_runner(monkeypatch: MonkeyPatch, result: FakeRunnerResult):
    captured: dict[str, object] = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return result

    monkeypatch.setitem(sys.modules, "ansible_runner", SimpleNamespace(run=fake_run))
    return captured


def test_access_run_returns_empty_facts_without_docker_container(monkeypatch):
    result = FakeRunnerResult(events=[{"event": "ok"}])
    captured = _install_fake_ansible_runner(monkeypatch, result)
    logger = Mock()

    fake_status_logger = Mock()
    fake_status_logger.isEnabledFor.return_value = False
    monkeypatch.setattr(
        "exasol.ansible.access.get_status_logger", lambda _: fake_status_logger
    )

    facts = Access.run(
        private_data_dir="/tmp/work",
        playbook=ansible.Playbook(file="play.yml", vars={"x": 1}),
        event_logger=logger,
    )

    assert facts.as_dict({}) == {}
    assert captured["quiet"] is True
    assert captured["playbook"] == "play.yml"
    assert captured["extravars"] == {"x": 1}
    logger.assert_called_once()


def test_access_run_returns_fact_cache_for_docker_container(monkeypatch):
    result = FakeRunnerResult(
        events=[],
        fact_cache={"host-1": {"dss_facts": {"name": "value"}}},
    )
    captured = _install_fake_ansible_runner(monkeypatch, result)

    fake_status_logger = Mock()
    fake_status_logger.isEnabledFor.return_value = True
    monkeypatch.setattr("exasol.ansible.access.get_status_logger", lambda _: fake_status_logger)

    facts = Access.run(
        private_data_dir="/tmp/work",
        playbook=ansible.Playbook(file="play.yml", vars={"docker_container": "host-1"}),
        event_logger=Mock(),
        event_handler=Mock(),
    )

    assert captured["quiet"] is False
    assert facts.get("name") == "value"


def test_access_run_raises_for_non_zero_return_code(monkeypatch):
    result = FakeRunnerResult(rc=5)
    _install_fake_ansible_runner(monkeypatch, result)
    monkeypatch.setattr(
        "exasol.ansible.access.get_status_logger",
        lambda _: Mock(isEnabledFor=Mock(return_value=False)),
    )

    with pytest.raises(AnsibleException) as ex:
        Access.run(
            private_data_dir="/tmp/work",
            playbook=ansible.Playbook(file="play.yml"),
            event_logger=Mock(),
        )
    assert ex.value.args == (5,)


def test_runner_event_handler_handles_missing_and_invalid_event_data(tmp_path):
    runner = Runner(Mock(), tmp_path)

    assert runner.event_handler(Event({})) is False
    assert runner.event_handler(Event({"event_data": "invalid"})) is False


def test_runner_event_handler_logs_long_duration(tmp_path):
    runner = Runner(Mock(), tmp_path)
    runner._duration_logger.debug = Mock()

    assert runner.event_handler(Event({"event_data": {"duration": 2.6}}))
    runner._duration_logger.debug.assert_called_once_with("duration: 3 seconds")


def test_runner_event_handler_ignores_short_duration(tmp_path):
    runner = Runner(Mock(), tmp_path)
    runner._duration_logger.debug = Mock()

    assert runner.event_handler(Event({"event_data": {"duration": 1.0}}))
    runner._duration_logger.debug.assert_not_called()


def test_runner_duration_logger_reuses_existing_duration_handler():
    logger_1 = Runner.duration_logger()
    handler_count = len(logger_1.handlers)

    logger_2 = Runner.duration_logger()

    assert logger_1 is logger_2
    assert len(logger_2.handlers) == handler_count


def test_runner_inventory_renders_host_without_private_key(tmp_path):
    ansible_access = Mock()
    ansible_access.run.return_value = ansible.Facts({})
    runner = Runner(ansible_access, tmp_path)

    runner.run(
        ansible.Playbook(file="play.yml"),
        hosts=(ansible.InventoryHost("plain-host"),),
    )

    assert (tmp_path / "inventory").read_text(encoding="utf-8") == (
        "[test_targets]\n\nplain-host\n\n"
    )


def test_importlib_directory_asset_ignores_nested_pycache_and_copies_subdirs(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "tasks").mkdir()
    (source / "tasks" / "main.yml").write_text("ok", encoding="utf-8")
    (source / "__pycache__").mkdir()
    (source / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")

    asset = ImportlibDirectoryAsset(source, Path("roles"))

    paths = asset.paths()
    assert Path("roles/__pycache__") not in paths
    assert paths[Path("roles")] == "directory"
    assert paths[Path("roles/tasks")] == "directory"
    assert paths[Path("roles/tasks/main.yml")] == "file"

    target = tmp_path / "target"
    target.mkdir()
    asset.copy_to(target)

    assert (target / "roles" / "tasks" / "main.yml").read_text(encoding="utf-8") == "ok"


def test_package_exports_and_version_constants():
    version = importlib.import_module("exasol.ansible.version")

    assert ansible.Access is not None
    assert ansible.Context is not None
    assert ansible.Facts is not None
    assert ansible.ImportlibRepository is not None
    assert ansible.InventoryHost is not None
    assert ansible.Playbook is not None
    assert ansible.Repository is not None
    assert ansible.Runner is not None
    assert ansible.Facts is Facts
    assert version.VERSION == "0.1.0"
    assert version.__version__ == version.VERSION
    assert version.MAJOR == 0
    assert version.MINOR == 1
    assert version.PATCH == 0
