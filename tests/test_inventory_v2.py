"""Adversarial tests for frozen inventory methodology version 2."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from inventory.inventory_v2 import scan
from inventory.models import INVENTORY_METHODOLOGY_VERSION_V2, Bucket

FIXTURE = Path(__file__).parent / "fixtures" / "inventory_v2_adversarial.c"


class InventoryV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        (root / "src").mkdir()
        (root / "src" / "fixture.c").write_text(FIXTURE.read_text(), encoding="utf-8")
        self.records = {item.name: item for item in scan(root, "src", "synthetic", "v2")}

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_static_scope_and_arrays(self) -> None:
        self.assertFalse(self.records["file_static_function"].features["static_local"])
        self.assertFalse(self.records["file_global"].features["static_local"])
        self.assertTrue(self.records["true_local_static"].features["static_local"])
        self.assertTrue(self.records["Flexible"].features["flexible_array"])
        self.assertFalse(self.records["array_parameter"].features["flexible_array"])
        self.assertFalse(self.records["fixed_array"].features["flexible_array"])

    def test_sanitizing_and_scoped_preprocessing(self) -> None:
        record = self.records["comment_and_string"]
        for feature in ("flexible_array", "goto", "union", "memcpy"):
            self.assertFalse(record.features[feature])
        self.assertFalse(self.records["file_static_function"].features["conditional_compilation"])
        self.assertTrue(self.records["nested_conditional"].features["conditional_compilation"])
        self.assertTrue(self.records["under_conditional"].features["conditional_compilation"])
        self.assertTrue(self.records["macro_inside"].features["macro_use"])

    def test_unknown_and_extern(self) -> None:
        macro = next(item for item in self.records.values() if item.kind == "macro_generated_declaration")
        self.assertEqual((macro.bucket, macro.confidence), (Bucket.UNKNOWN, "low"))
        external = self.records["external_value"]
        self.assertNotEqual(external.bucket, Bucket.BOUNDARY)
        self.assertTrue(external.features["extern_declaration"])
        self.assertEqual(INVENTORY_METHODOLOGY_VERSION_V2, 2)
