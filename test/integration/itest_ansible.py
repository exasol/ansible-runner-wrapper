from test.integration.docker_utils import exec_run

import exasol.ansible as ansible


def test_x1(docker_container):
    host = docker_container.name
    print(f'running docker_container {host}')
    output = exec_run(docker_container, "ls -d /tmp")
    print(f'output: {output}')


def test_integration(docker_container_with_python3):
    container = docker_container_with_python3
    host_name = container.name
    sample_directory = "/tmp/sample-directory"
    extra_vars = {
        "docker_container": host_name,
        "sample_dir": sample_directory,
    }
    playbook = ansible.Playbook("docker_playbook.yml", vars=extra_vars)
    repositories = (ansible.ImportlibRepository("test.resources.itest"),)
    host = ansible.InventoryHost(host_name=host_name)

    with ansible.Context(ansible.Access(), repositories) as runner:
        raw_facts = runner.run(playbook, hosts=(host,), retrieve_facts_from=host_name)

    facts = ansible.Facts(raw_facts, prefixes=["my_facts"])
    assert facts.get("sample_fact") == sample_directory
    path = exec_run(container, f"ls -d {sample_directory}")
    assert path == sample_directory
