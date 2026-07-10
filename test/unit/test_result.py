import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

import exasol.ansible as ansible
from exasol.ansible.result import _normalize_ansible_value


def create_result(
    tmp_path: Path,
    inline_cache: dict | None = None,
    fact_cache_prefix: str = "s1_",
    events: list[dict] | tuple[dict, ...] | None = None,
) -> ansible.Result:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir(exist_ok=True)
    return ansible.Result.from_runner(
        SimpleNamespace(
            config=SimpleNamespace(
                fact_cache=str(fact_cache_dir), fact_cache_prefix=fact_cache_prefix
            ),
            events=events or [],
            rc=0,
            get_fact_cache=lambda host: inline_cache or {},
        )
    )


def test_events_returns_snapshotted_runner_events(tmp_path: Path) -> None:
    events = (
        {"event": "playbook_on_start"},
        {"event": "runner_on_ok", "event_data": {"task": "Set facts"}},
    )
    result = create_result(tmp_path, events=events)

    assert result.events == events


def test_events_snapshot_consumes_one_shot_runner_iterable(tmp_path: Path) -> None:
    source_events = [
        {"event": "playbook_on_play_start", "event_data": {"play": "Sample Tasks"}},
        {"event": "runner_on_ok", "event_data": {"task": "Create directory"}},
    ]
    result = create_result(tmp_path, events=iter(source_events))

    assert result.events == tuple(source_events)
    assert tuple(result.events) == tuple(source_events)


def test_get_facts_supports_legacy_ansible_runner_output(tmp_path: Path) -> None:
    result = create_result(
        tmp_path, inline_cache={"my_facts": {"sample_fact": "value"}}
    )

    with pytest.warns(
        UserWarning, match="Result.get_facts\\(\\) relies on internal Ansible APIs"
    ):
        actual = result.get_facts("ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "value"}}


def test_get_facts_supports_ansible_14_fact_cache_format(tmp_path: Path) -> None:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir()
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
    (fact_cache_dir / "s1_ARW_ITEST").write_text(json.dumps(payload))
    result = create_result(tmp_path)

    with pytest.warns(UserWarning, match="Prefer stats instead of facts"):
        actual = result.get_facts("ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "/tmp/sample-directory"}}


def test_get_facts_returns_empty_when_cache_dir_is_missing(tmp_path: Path) -> None:
    result = ansible.Result.from_runner(
        SimpleNamespace(
            config=SimpleNamespace(fact_cache=str(tmp_path / "missing")),
            events=[],
            rc=0,
            get_fact_cache=lambda host: {},
        )
    )

    with pytest.warns(UserWarning):
        actual = result.get_facts("ARW_ITEST")

    assert actual == {}


def test_get_facts_returns_empty_when_host_cache_file_is_missing(
    tmp_path: Path,
) -> None:
    result = create_result(tmp_path)
    (tmp_path / "fact_cache" / "s1_OTHER").write_text("{}")

    with pytest.warns(UserWarning):
        actual = result.get_facts("ARW_ITEST")

    assert actual == {}


def test_get_facts_still_work_after_fact_cache_directory_is_removed(
    tmp_path: Path,
) -> None:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir()
    payload = {
        "__payload__": json.dumps(
            {
                "my_facts": {
                    "value": {"sample_fact": "value"},
                    "__ansible_type": "_AnsibleTaggedDict",
                    "tags": [],
                }
            }
        )
    }
    (fact_cache_dir / "s1_ARW_ITEST").write_text(json.dumps(payload))
    result = ansible.Result.from_runner(
        SimpleNamespace(
            config=SimpleNamespace(
                fact_cache=str(fact_cache_dir), fact_cache_prefix="s1_"
            ),
            events=[],
            rc=0,
            get_fact_cache=lambda host: {},
        )
    )

    shutil.rmtree(fact_cache_dir)

    with pytest.warns(UserWarning):
        actual = result.get_facts("ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "value"}}


def test_result_constructor_is_private(tmp_path: Path) -> None:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir()

    with pytest.raises(TypeError, match="Use Result.from_runner\\(\\)"):
        ansible.Result(
            SimpleNamespace(
                config=SimpleNamespace(
                    fact_cache=str(fact_cache_dir), fact_cache_prefix="s1_"
                ),
                events=[],
                rc=0,
                get_fact_cache=lambda host: {},
            ),
            (),
            "s1_",
            {},
        )


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


def test_normalize_ansible_value_does_not_unwrap_plain_value_dicts() -> None:
    value = {
        "result": {
            "value": 1,
        }
    }

    actual = _normalize_ansible_value(value)

    assert actual == value


def test_normalize_ansible_value_preserves_plain_payload_dicts() -> None:
    value = {
        "token": {
            "__payload__": "abc",
        }
    }

    actual = _normalize_ansible_value(value)

    assert actual == value


def test_get_facts_supports_custom_fact_cache_prefix(tmp_path: Path) -> None:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir()
    payload = {
        "__payload__": json.dumps(
            {
                "my_facts": {
                    "value": {"sample_fact": "value"},
                    "__ansible_type": "_AnsibleTaggedDict",
                    "tags": [],
                }
            }
        )
    }
    (fact_cache_dir / "prod-ARW_ITEST").write_text(json.dumps(payload))
    result = create_result(tmp_path, fact_cache_prefix="prod-")

    with pytest.warns(UserWarning):
        actual = result.get_facts("ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "value"}}
