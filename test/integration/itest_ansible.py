from test.integration.docker_utils import exec_run

import exasol.ansible as ansible


def run_lifecycle_playbook(arw_itest_docker_container) -> tuple[object, str, str]:
    container = arw_itest_docker_container
    host_name = container.name
    sample_directory = "/tmp/sample-directory"
    extravars = {
        "docker_container": host_name,
        "sample_dir": sample_directory,
    }
    playbook = ansible.Playbook("docker_playbook.yml", vars=extravars)
    repositories = (ansible.ImportlibRepository("test.resources.itest"),)
    runner = ansible.Runner(repositories=repositories)
    return runner.run(playbook), host_name, sample_directory


def test_lifecycle(arw_itest_docker_container):
    """
    Use a specific playbook and some extra vars to manage a Docker
    container as Ansible host.

    The playbook will create the directory specified by the extra vars and
    populate some Ansible facts.

    After Ansible has terminated, the test verifies the facts being populated
    and verifies that the directory has been created.
    """

    # Prepare all components and settings for running Ansible
    container = arw_itest_docker_container
    result, host_name, sample_directory = run_lifecycle_playbook(container)
    raw_facts = result.get_facts(host_name)

    # Verify populated Ansible facts
    facts = ansible.Facts(raw_facts, prefixes=["my_facts"])
    assert facts.get("sample_fact") == sample_directory

    # Inspect the Docker container to verify that directory has been created
    path = exec_run(container, f"ls -d {sample_directory}")
    assert path == sample_directory


def test_result_exposes_events(arw_itest_docker_container):
    result, host_name, _ = run_lifecycle_playbook(arw_itest_docker_container)
    saw_sample_tasks_play = False
    saw_set_facts = False
    saw_create_directory = False

    for event in result.events:
        event_data = event.get("event_data", {})
        if (
            event.get("event") == "playbook_on_play_start"
            and event_data.get("play") == "Sample Tasks"
        ):
            saw_sample_tasks_play = True
        if (
            event.get("event") == "runner_on_ok"
            and event_data.get("task") == "Set facts"
            and event_data.get("host") == host_name
        ):
            saw_set_facts = True
        if (
            event.get("event") == "runner_on_ok"
            and event_data.get("task") == "Create directory"
            and event_data.get("host") == host_name
        ):
            saw_create_directory = True
        if saw_sample_tasks_play and saw_set_facts and saw_create_directory:
            break

    assert saw_sample_tasks_play
    assert saw_set_facts
    assert saw_create_directory
