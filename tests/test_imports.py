"""Smoke tests for the placeholder Python packages."""


def test_inventory_package_imports() -> None:
    import inventory

    assert inventory.__doc__
