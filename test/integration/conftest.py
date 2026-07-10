import io
import logging
import os
import uuid
from collections.abc import Iterable
from inspect import cleandoc

import docker
import pytest
from docker.errors import DockerException
from docker.models.containers import Container as DockerContainer

LOG = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def arw_itest_docker_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
    except (DockerException, OSError, PermissionError) as exception:
        docker_host = os.environ.get("DOCKER_HOST", "<unset>")
        pytest.fail(
            "Integration tests require Docker access. "
            f"Could not connect to the Docker daemon via DOCKER_HOST={docker_host!r}: {exception}. "
            "If Docker is available on this machine, rerun the tests in an environment that allows access "
            "to the Docker socket."
        )
    return client


@pytest.fixture(scope="session")
def arw_itest_docker_image(arw_itest_docker_client: docker.DockerClient) -> str:
    image_name = "arw/itest:latest"
    LOG.info("Creating Docker image %s", image_name)
    install_args = "--no-install-recommends --assume-yes python3 python3-pexpect"
    docker_file_content = cleandoc(f"""
        FROM ubuntu:24.04
        ENV DEBIAN_FRONTEND noninteractive
        RUN apt-get update && apt-get install {install_args}
        """)
    stream = io.BytesIO(docker_file_content.encode("utf-8"))
    arw_itest_docker_client.images.build(fileobj=stream, tag=image_name, rm=True)
    return image_name


@pytest.fixture(scope="session")
def arw_itest_docker_container(
    arw_itest_docker_client: docker.DockerClient,
    arw_itest_docker_image: str,
) -> Iterable[DockerContainer]:
    """
    Run a docker container.

    The name of the returned container can be used as host to be managed by
    ansible in integration tests.
    """

    name = f"ARW_ITEST_{uuid.uuid4().hex[:8]}"
    image = arw_itest_docker_image
    container = None
    try:
        LOG.info("Starting Docker container %s of image %s", name, image)
        container = arw_itest_docker_client.containers.create(
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
