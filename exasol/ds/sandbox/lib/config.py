try:
    from importlib.metadata import (
        PackageNotFoundError,
        version,
    )
except ImportError:  # pragma: no cover
    from importlib_metadata import (
        PackageNotFoundError,
        version,
    )

try:
    # name of the project as specified in file pyproject.toml
    ANSIBLE_RUNNER_WRAPPER_VERSION = version("exasol-ansible-runner-wrapper")
except PackageNotFoundError:  # pragma: no cover
    ANSIBLE_RUNNER_WRAPPER_VERSION = "0.0.0+local"

_default_config = {
    # unit: seconds
    "time_to_wait_for_polling": 60.0,
    "ansible_runner_wrapper_version": ANSIBLE_RUNNER_WRAPPER_VERSION,
}


class ConfigObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


default_config_object = ConfigObject(**_default_config)
