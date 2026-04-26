import logging

from docker.models.containers import Container as DockerContainer

LOG = logging.getLogger(__name__)


def exec_run(container: DockerContainer, command: str, log: bool = False) -> str:
    log and LOG.info(command)
    exit_code, output = container.exec_run(command)
    decoded = output.decode("utf-8").strip()
    if exit_code != 0:
        raise RuntimeError(
            f"Command {command} returned {exit_code} with output\n{decoded}"
        )
    return decoded
