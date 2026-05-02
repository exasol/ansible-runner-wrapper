from test.integration.docker_utils import exec_run

import exasol.ansible as ansible

import pytest


def test_lifecycle(docker_container_with_python3):
    """
    Use a specific playbook and some extra vars to manage a Docker
    container as Ansible host.

    The playbook will create the directory specified by the extra vars and
    populate some Ansible facts.

    After Ansible has terminated, the test verifies the facts being populated
    and verifies that the directory has been created.
    """

    # Prepare all components and settings for running Ansible
    container = docker_container_with_python3
    host_name = container.name
    sample_directory = "/tmp/sample-directory"
    extra_vars = {
        "docker_container": host_name,
        "sample_dir": sample_directory,
    }
    playbook = ansible.Playbook("docker_playbook.yml", vars=extra_vars)
    repositories = (ansible.ImportlibRepository("test.resources.itest"),)

    # Run ansible
    with ansible.Context(ansible.Access(), repositories) as runner:
        raw_facts = runner.run(playbook, retrieve_facts_from=host_name)

    # Verify populated Ansible facts
    facts = ansible.Facts(raw_facts, prefixes=["my_facts"])
    assert facts.get("sample_fact") == sample_directory

    # Inspect the Docker container to verify that directory has been created
    path = exec_run(container, f"ls -d {sample_directory}")
    assert path == sample_directory
