import json
from pathlib import Path
from types import SimpleNamespace

from exasol.ansible.runner import _retrieve_fact_cache


def create_result(
    tmp_path: Path,
    inline_cache: dict | None = None,
) -> SimpleNamespace:
    fact_cache_dir = tmp_path / "fact_cache"
    fact_cache_dir.mkdir()
    return SimpleNamespace(
        config=SimpleNamespace(fact_cache=str(fact_cache_dir)),
        get_fact_cache=lambda host: inline_cache or {},
    )


def test_retrieve_fact_cache_supports_legacy_ansible_runner_output(tmp_path: Path) -> None:
    result = create_result(tmp_path, inline_cache={"my_facts": {"sample_fact": "value"}})

    actual = _retrieve_fact_cache(result, "ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "value"}}


def test_retrieve_fact_cache_supports_ansible_14_fact_cache_format(tmp_path: Path) -> None:
    result = create_result(tmp_path)
    payload = {
        "__payload__": json.dumps(
            {
                "my_facts": {
                    "value": {
                        "sample_fact": {
                            "value": "/tmp/sample-directory",
                            "__ansible_type": "_AnsibleTaggedStr",
                            "tags": [],
                        }
                    },
                    "__ansible_type": "_AnsibleTaggedDict",
                    "tags": [],
                }
            }
        )
    }
    (tmp_path / "fact_cache" / "s1_ARW_ITEST").write_text(json.dumps(payload))

    actual = _retrieve_fact_cache(result, "ARW_ITEST")

    assert actual == {"my_facts": {"sample_fact": "/tmp/sample-directory"}}
