import logging
from test.integration.docker_utils import exec_run

import docker
import pytest

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@pytest.fixture(scope="session")
def docker_container() -> str:
    """
    Run a docker container.

    The name of the returned container can be used as host to be managed by
    ansible in integration tests.
    """

    client = docker.from_env()
    image = "ubuntu:latest"
    name = "ARW_ITEST"
    container = None
    try:
        LOG.debug("Starting container %s of image %s", name, image)
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
            LOG.debug("Stopping container %s of image %s", name, image)
            container.stop()
            LOG.debug("Removing container %s of image %s", name, image)
            container.remove()
            LOG.debug("Done")


@pytest.fixture(scope="session")
def docker_container_with_python3(docker_container):
    exec_run(docker_container, "apt-get update")
    exec_run(
        docker_container,
        "apt-get install --no-install-recommends "
        "--assume-yes python3 python3-pexpect",
    )
    return docker_container
