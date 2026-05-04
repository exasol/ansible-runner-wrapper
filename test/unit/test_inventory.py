import exasol.ansible.inventory as inventory


def test_render() -> None:
    hosts = (
        inventory.InventoryHost("H1"),
        inventory.InventoryHost("H2", "key"),
    )
    actual = inventory.render(hosts)
    assert actual == (
        f"[{inventory.INVENTORY_GROUP}]\n\n"
        "H1\n"
        "H2 ansible_ssh_private_key_file=key\n"
        "\n"
    )
