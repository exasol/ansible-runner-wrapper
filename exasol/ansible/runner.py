import json
import logging
from pathlib import Path
from typing import (
    Any,
    NewType,
)

# import the real final ansible runner from
# https://pypi.org/project/ansible-runner/
# https://github.com/ansible/ansible-runner
# https://docs.ansible.com/projects/runner/en/latest/python_interface/
import ansible_runner  # type: ignore[import-untyped]

import exasol.ansible.inventory as inventory
from exasol.ansible.context import copy_files
from exasol.ansible.facts import Facts
from exasol.ansible.playbook import Playbook
from exasol.ansible.repository import Repository

logger = logging.getLogger(__name__)

Event = NewType("Event", dict[str, Any])


class AnsibleException(RuntimeError):
    pass


def _remove_ansible_tags(value: Any) -> Any:
    if isinstance(value, dict):
        if "__ansible_type" in value and "value" in value:
            return _remove_ansible_tags(value["value"])
        return {key: _remove_ansible_tags(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_remove_ansible_tags(item) for item in value]
    return value


def _decode_fact_cache(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    payload = value.get("__payload__")
    if isinstance(payload, str):
        return _remove_ansible_tags(json.loads(payload))
    return _remove_ansible_tags(value)


def _read_fact_cache_file(path: Path) -> dict[str, Any]:
    return _decode_fact_cache(json.loads(path.read_text()))


def _find_fact_cache_file(cache_dir: Path, host: str) -> Path | None:
    if not cache_dir.is_dir():
        return None

    direct = cache_dir / host
    if direct.exists():
        return direct

    for candidate in cache_dir.iterdir():
        prefix, separator, name = candidate.name.partition("_")
        if (
            separator
            and name == host
            and prefix.startswith("s")
            and prefix[1:].isdigit()
        ):
            return candidate

    return None


def _get_fact_cache(result: Any, host: str) -> dict[str, Any]:
    facts = _decode_fact_cache(result.get_fact_cache(host))
    if facts:
        return facts

    if fact_cache := getattr(getattr(result, "config", None), "fact_cache", None):
        cache_dir = Path(fact_cache)
    else:
        return facts

    if cache_file := _find_fact_cache_file(cache_dir, host):
        return _read_fact_cache_file(cache_file)

    return facts


class Runner:
    def __init__(
        self,
        repositories: tuple[Repository, ...],
        work_dir: Path | None = None,
    ):
        self._repos = repositories
        self._path = work_dir

    def event_handler(self, event: Event) -> bool:
        duration = Facts(event).get("event_data", "duration")
        if type(duration) not in (int, float):
            return False  # nothing to process

        if duration > 1.5:
            logger.info("duration: %s seconds", round(duration))

        return True

    def run(
        self,
        playbook: Playbook,
        hosts: tuple[inventory.Host, ...] = (),
        retrieve_facts_from: str = "",
    ) -> dict[str, Any]:
        quiet = not logger.isEnabledFor(logging.INFO)
        event_handler = None if quiet else self.event_handler
        with copy_files(repositories=self._repos, work_dir=self._path) as work_dir:
            content = inventory.render(hosts)
            (work_dir / "inventory").write_text(content)
            result = ansible_runner.run(
                private_data_dir=str(work_dir),
                playbook=playbook.file,
                quiet=quiet,
                event_handler=event_handler,
                extravars=playbook.vars,
            )

            for event in result.events:
                logger.debug(json.dumps(event, indent=2))

            if result.rc != 0:
                raise AnsibleException(result.rc)

            if host := retrieve_facts_from:
                return _get_fact_cache(result, host)
            else:
                return {}
