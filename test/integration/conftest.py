import logging
from collections.abc import Iterable
from test.integration.docker_utils import exec_run

import docker
import pytest
from docker.models.containers import Container as DockerContainer

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@pytest.fixture(scope="session")
def docker_container() -> Iterable[DockerContainer]:
    """
    Run a docker container.

    The name of the returned container can be used as host to be managed by
    ansible in integration tests.
    """

    client = docker.from_env()
    image = "ubuntu:22.04"
    name = "ARW_ITEST"
    container = None
    try:
        LOG.info("Starting container %s of image %s", name, image)
        container = client.containers.create(
            image=image,
            name=name,
            command="sleep infinity",
            detach=True,
        )
        container.start()
        yield container
    finally:
        if container:
            LOG.info("Stopping container")
            container.stop()
            LOG.info("Removing container")
            container.remove()
            LOG.info("Done")


@pytest.fixture(scope="session")
def docker_container_with_python3(docker_container) -> Iterable[DockerContainer]:
    """
    Ansible automation requires Python to be installed on the host to
    manage.
    """

    exec_run(docker_container, "apt-get update", log=True)
    exec_run(
        docker_container,
        "apt-get install --no-install-recommends "
        "--assume-yes python3 python3-pexpect",
        log=True,
    )
    return docker_container
