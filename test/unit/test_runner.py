import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import exasol.ansible as ansible
from exasol.ansible.runner import (
    AnsibleException,
    Runner,
    _normalize_ansible_value,
    _retrieve_fact_cache,
    ansible_runner,
)


def create_result(
    tmp_path: Path,
    inline_cache: dict | None = None,
) -> SimpleNamespace:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir()
    return SimpleNamespace(
        config=SimpleNamespace(fact_cache=str(fact_cache_dir)),
        get_fact_cache=lambda host: inline_cache or {},
    )


def test_retrieve_fact_cache_supports_legacy_ansible_runner_output(tmp_path: Path) -> None:
    result = create_result(tmp_path, inline_cache={"my_facts": {"sample_fact": "value"}})

    actual = _retrieve_fact_cache(result, "ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "value"}}


def test_retrieve_fact_cache_supports_ansible_14_fact_cache_format(tmp_path: Path) -> None:
    result = create_result(tmp_path)
    payload = {
        "__payload__": json.dumps(
            {
                "my_facts": {
                    "value": {
                        "sample_fact": {
                            "value": "/tmp/sample-directory",
                            "__ansible_type": "_AnsibleTaggedStr",
                            "tags": [],
                        }
                    },
                    "__ansible_type": "_AnsibleTaggedDict",
                    "tags": [],
                }
            }
        )
    }
    (tmp_path / "fact_cache" / "s1_ARW_ITEST").write_text(json.dumps(payload))

    actual = _retrieve_fact_cache(result, "ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "/tmp/sample-directory"}}


def test_retrieve_fact_cache_returns_empty_when_cache_dir_is_missing(tmp_path: Path) -> None:
    result = SimpleNamespace(
        config=SimpleNamespace(fact_cache=str(tmp_path / "missing")),
        get_fact_cache=lambda host: {},
    )

    actual = _retrieve_fact_cache(result, "ARW_ITEST")

    assert actual == {}


def test_retrieve_fact_cache_returns_empty_when_host_cache_file_is_missing(tmp_path: Path) -> None:
    result = create_result(tmp_path)
    (tmp_path / "fact_cache" / "s1_OTHER").write_text("{}")

    actual = _retrieve_fact_cache(result, "ARW_ITEST")

    assert actual == {}


def test_normalize_ansible_value_preserves_plain_dict_entries_and_lists() -> None:
    value = {
        "plain": "text",
        "tagged": {
            "value": "normalized",
            "__ansible_type": "_AnsibleTaggedStr",
            "tags": [],
        },
        "items": [
            {
                "value": 42,
                "__ansible_type": "_AnsibleTaggedInt",
                "tags": [],
            }
        ],
        "tags": ["ignored"],
    }

    actual = _normalize_ansible_value(value)

    assert actual == {"plain": "text", "tagged": "normalized", "items": [42]}


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


def test_run_returns_empty_dict_when_fact_retrieval_is_not_requested(
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

    assert actual == {}
