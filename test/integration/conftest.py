import io
import logging
from collections.abc import Iterable
from inspect import cleandoc

import docker
import pytest
from docker.models.containers import Container as DockerContainer

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@pytest.fixture(scope="session")
def arw_itest_docker_image() -> str:
    image_name = "arw/itest:latest"
    LOG.info("Creating Docker image %s", image_name)
    install_args = "--no-install-recommends --assume-yes python3 python3-pexpect"
    docker_file_content = cleandoc(f"""
        FROM ubuntu:24.04
        ENV DEBIAN_FRONTEND noninteractive
        RUN apt-get update && apt-get install {install_args}
        """)
    stream = io.BytesIO(docker_file_content.encode("utf-8"))
    client = docker.from_env()
    client.images.build(fileobj=stream, tag=image_name, rm=True)
    return image_name


@pytest.fixture(scope="session")
def arw_itest_docker_container(arw_itest_docker_image) -> Iterable[DockerContainer]:
    """
    Run a docker container.

    The name of the returned container can be used as host to be managed by
    ansible in integration tests.
    """

    client = docker.from_env()
    name = "ARW_ITEST"
    image = arw_itest_docker_image
    container = None
    try:
        LOG.info("Starting Docker container %s of image %s", name, image)
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
