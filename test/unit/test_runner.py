import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import exasol.ansible as ansible
from exasol.ansible.runner import (
    AnsibleException,
    Runner,
    ansible_runner,
)


def test_event_handler_returns_false_without_numeric_duration() -> None:
    runner = Runner(repositories=())

    actual = runner.event_handler({"event_data": {"duration": "slow"}})

    assert actual is False


def test_event_handler_logs_slow_events(caplog: pytest.LogCaptureFixture) -> None:
    runner = Runner(repositories=())

    with caplog.at_level(logging.INFO):
        actual = runner.event_handler({"event_data": {"duration": 1.8}})

    assert actual is True
    assert "duration: 2 seconds" in caplog.text


def test_run_raises_ansible_exception_on_non_zero_return_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = SimpleNamespace(events=[], rc=1)
    monkeypatch.setattr(ansible_runner, "run", Mock(return_value=result))
    runner = ansible.Runner(
        repositories=(ansible.ImportlibRepository("test.resources.simple"),),
        work_dir=tmp_path,
    )

    with pytest.raises(AnsibleException):
        runner.run(ansible.Playbook("playbook.yml"))


def test_run_returns_result_object(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = SimpleNamespace(events=[], rc=0)
    monkeypatch.setattr(ansible_runner, "run", Mock(return_value=result))
    runner = ansible.Runner(
        repositories=(ansible.ImportlibRepository("test.resources.simple"),),
        work_dir=tmp_path,
    )

    actual = runner.run(ansible.Playbook("playbook.yml"))

    assert isinstance(actual, ansible.Result)
