import json
import logging
from collections.abc import Callable
from typing import (
    Any,
    NewType,
)

# import the real final ansible runner from
# https://pypi.org/project/ansible-runner/
# https://github.com/ansible/ansible-runner
# https://docs.ansible.com/projects/runner/en/latest/python_interface/
from exasol.ansible.facts import Facts
from exasol.ansible.playbook import Playbook
from exasol.ds.sandbox.lib.logging import (
    LogType,
    get_status_logger,
)

Event = NewType("Event", dict[str, Any])


class AnsibleException(RuntimeError):
    pass


class Access:
    """
    Provides access to ansible runner.
    @raises: AnsibleException if ansible execution fails
    """

    @staticmethod
    def run(
        private_data_dir: str,
        playbook: Playbook,
        event_logger: Callable[[str], None],
        event_handler: Callable[[Event], bool] | None = None,
    ) -> Facts:
        import ansible_runner

        quiet = not get_status_logger(LogType.ANSIBLE).isEnabledFor(logging.INFO)
        runner = ansible_runner.run(
            private_data_dir=private_data_dir,
            playbook=playbook.file,
            quiet=quiet,
            event_handler=event_handler,
            extravars=playbook.vars,
        )

        for event in runner.events:
            event_logger(json.dumps(event, indent=2))

        if runner.rc != 0:
            raise AnsibleException(runner.rc)

        if "docker_container" not in playbook.vars:
            return Facts({})

        host = playbook.vars["docker_container"]
        fact_cache = runner.get_fact_cache(host)
        return Facts(fact_cache)
