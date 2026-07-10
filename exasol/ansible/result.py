import json
import os
import warnings
from pathlib import Path
from typing import Any

import ansible_runner  # type: ignore[import-untyped]


def _normalize_ansible_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_ansible_value(item) for item in value]

    if not isinstance(value, dict):
        return value

    if (
        set(value).issubset({"value", "tags", "__ansible_type"})
        and "value" in value
        and "__ansible_type" in value
    ):
        return _normalize_ansible_value(value["value"])

    return {
        key: _normalize_ansible_value(item)
        for key, item in value.items()
        if key != "tags"
    }


def _read_fact_cache_file(path: Path) -> dict[str, Any]:
    content = json.loads(path.read_text())
    if isinstance(content, dict) and set(content) == {"__payload__"}:
        content = json.loads(content["__payload__"])
    return _normalize_ansible_value(content)


class Result:
    def __init__(
        self,
        runner: ansible_runner.Runner,
        fact_cache_prefix: str,
        fact_cache_entries: dict[str, dict[str, Any]],
        *,
        _internal: bool = False,
    ):
        if not _internal:
            raise TypeError("Use Result.from_runner() to create Result instances.")
        self._runner = runner
        self._fact_cache_prefix = fact_cache_prefix
        self._fact_cache_entries = fact_cache_entries

    @staticmethod
    def from_runner(runner: ansible_runner.Runner) -> "Result":
        config = getattr(runner, "config", None)
        fact_cache = getattr(config, "fact_cache", "")
        fact_cache_prefix = getattr(config, "fact_cache_prefix", "")
        if not isinstance(fact_cache_prefix, str):
            fact_cache_prefix = ""
        fact_cache_entries = {}
        if fact_cache and isinstance(fact_cache, (str, os.PathLike)):
            fact_cache_entries = Result._snapshot_fact_cache_dir(Path(fact_cache))
        return Result(
            runner,
            fact_cache_prefix,
            fact_cache_entries,
            _internal=True,
        )

    @property
    def events(self):
        return self._runner.events

    @property
    def rc(self) -> int:
        return self._runner.rc

    def get_facts(self, host: str) -> dict[str, Any]:
        """Retrieve facts for a host from ansible-runner output."""
        warnings.warn(
            "Result.get_facts() relies on internal Ansible APIs and file formats, "
            "so it may break with future Ansible changes. Prefer stats instead of "
            "facts once https://github.com/exasol/ansible-runner-wrapper/issues/44 "
            "is implemented.",
            UserWarning,
            stacklevel=2,
        )
        raw_facts = self._runner.get_fact_cache(host)
        if raw_facts:
            return _normalize_ansible_value(raw_facts)

        candidate_names = [host]
        if self._fact_cache_prefix:
            candidate_names.insert(0, f"{self._fact_cache_prefix}{host}")

        for candidate_name in candidate_names:
            if candidate_name in self._fact_cache_entries:
                return self._fact_cache_entries[candidate_name]

        for candidate_name, content in self._fact_cache_entries.items():
            if candidate_name == host or candidate_name.endswith(f"_{host}"):
                return content

        return {}

    @staticmethod
    def _snapshot_fact_cache_dir(fact_cache_dir: Path) -> dict[str, dict[str, Any]]:
        if not fact_cache_dir.exists():
            return {}

        return {
            candidate.name: _read_fact_cache_file(candidate)
            for candidate in fact_cache_dir.iterdir()
            if candidate.is_file()
        }
