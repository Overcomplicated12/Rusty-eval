"""Smoke tests for the inventory package."""

import unittest


class ImportTests(unittest.TestCase):
    def test_inventory_package_imports(self) -> None:
        import inventory

        self.assertTrue(inventory.__doc__)
