import unittest

from v3.cpp_inventory.dedup import deduplicate_functions
from v3.cpp_inventory.scope import apply_scope


class PlaceholderTests(unittest.TestCase):
    def test_dedup_passes_records_through(self) -> None:
        records = [object()]
        self.assertEqual(deduplicate_functions(records), records)

    def test_scope_passes_records_through(self) -> None:
        records = [object()]
        self.assertEqual(apply_scope(records, object()), records)
