from docker.models.containers import Container as DockerContainer


def exec_run(container: DockerContainer, command: str) -> str:
    exit_code, output = container.exec_run(command)
    decoded = output.decode("utf-8").strip()
    if exit_code != 0:
        raise RuntimeError(
            f"Command {command} returned {exit_code} with output\n{decoded}"
        )
    return decoded
