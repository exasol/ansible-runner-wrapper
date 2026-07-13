from exasol.toolbox.util.version import Version

import exasol.ansible


def test_package_version_is_set():
    assert isinstance(exasol.ansible.__version__, str)
    assert Version.from_string(exasol.ansible.__version__)
