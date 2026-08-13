"""Smoke tests for the inventory package."""

import unittest


class ImportTests(unittest.TestCase):
    def test_inventory_package_imports(self) -> None:
        import inventory

        self.assertTrue(inventory.__doc__)

    def test_rust_baseline_package_imports(self) -> None:
        import rust_baseline

        self.assertTrue(rust_baseline.__doc__)
