from typing import Any

try:
    import importlib.metadata as importlib_metadata
except ImportError:  # pragma: no cover
    import importlib_metadata  # type: ignore[no-redef]

try:
    # name of the project as specified in file pyproject.toml
    ANSIBLE_RUNNER_WRAPPER_VERSION = importlib_metadata.version(
        "exasol-ansible-runner-wrapper"
    )
except importlib_metadata.PackageNotFoundError:  # pragma: no cover
    ANSIBLE_RUNNER_WRAPPER_VERSION = "0.0.0+local"

_default_config = {
    # unit: seconds
    "time_to_wait_for_polling": 60.0,
    "ansible_runner_wrapper_version": ANSIBLE_RUNNER_WRAPPER_VERSION,
}


class ConfigObject:
    time_to_wait_for_polling: float
    ansible_runner_wrapper_version: str

    def __init__(self, **kwargs: Any):
        self.__dict__.update(kwargs)


default_config_object = ConfigObject(**_default_config)
