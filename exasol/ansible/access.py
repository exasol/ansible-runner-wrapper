import json
import logging
from collections.abc import Callable
from typing import (
    Any,
    NewType,
)

from exasol.ansible.playbook import Playbook

# import the real final ansible runner from
# https://pypi.org/project/ansible-runner/
# https://github.com/ansible/ansible-runner
# https://docs.ansible.com/projects/runner/en/latest/python_interface/
import ansible_runner

from exasol.ds.sandbox.lib.logging import (
    LogType,
    get_status_logger,
)

Event = NewType("Event", dict[str, Any])


class AnsibleException(RuntimeError):
    pass


# For this class it is recommended to add an integration test.
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
        retrieve_facts_from: str = "",
    ) -> dict[str, Any]:
        """
        Run the actual ansible_runner.

        Args:
            retrieve_facts_from:
                Optional, host to retrieve the fact cache from after
                running ansible.
        """

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

        if host := retrieve_facts_from:
            return runner.get_fact_cache(host)
        else:
            return {}
