from typing import Any

import pytest

import exasol.ansible as ansible

PAYLOAD = {"a": {"b": {"c": "value"}}}


def create_facts(payload: dict[str, Any]) -> ansible.Facts:
    return ansible.Facts({"dss_facts": payload}, prefixes=["dss_facts"])


@pytest.fixture
def sample_facts() -> ansible.Facts:
    return create_facts(PAYLOAD)


@pytest.mark.parametrize(
    "keys, expected",
    [
        ([], PAYLOAD),
        (["missing"], None),
        (["a"], PAYLOAD["a"]),
        (["a", "b", "c"], "value"),
    ],
)
def test_ansible_facts(
    sample_facts: ansible.Facts,
    keys: list[str],
    expected: Any,
) -> None:
    assert sample_facts.get(*keys) == expected


def test_as_dict() -> None:
    payload = {
        "a": {"a1": "AA"},
        "b": {"b1": "BB"},
    }
    facts = create_facts(payload)
    spec = {
        "MISSING": ("c",),
        "VA": ("a", "a1"),
        "VB": ("b", "b1"),
    }
    actual = facts.as_dict(spec)
    expected = {"VA": "AA", "VB": "BB"}
    assert expected == actual
