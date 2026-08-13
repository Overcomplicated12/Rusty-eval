"""Synthetic tests for inventory methodology version 1."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from inventory.inventory import sample, scan, write_outputs
from inventory.models import INVENTORY_METHODOLOGY_VERSION, Bucket
from inventory.rules import classify

FIXTURE = Path(__file__).parent / "fixtures" / "inventory_v1.c"


class InventoryV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        source = self.root / "src"
        source.mkdir()
        (source / "fixture.c").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        self.records = scan(self.root, "src", "synthetic", "abc123")
        self.by_name = {record.name: record for record in self.records}

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_detects_required_features(self) -> None:
        self.assertTrue(self.by_name["pointer_ok"].features["raw_pointer_parameter"])
        self.assertTrue(self.by_name["pointer_math"].features["pointer_arithmetic"])
        self.assertTrue(self.by_name["double_pointer"].features["pointer_to_pointer"])
        self.assertTrue(self.by_name["void_ptr"].features["void_pointer"])
        self.assertTrue(self.by_name["copy"].features["memcpy"])
        self.assertTrue(self.by_name["allocate"].features["malloc"])
        self.assertTrue(self.by_name["allocate"].features["free"])
        self.assertTrue(self.by_name["array"].features["c_array"])
        self.assertTrue(self.by_name["callback"].features["function_pointer"])
        self.assertTrue(self.by_name["Value"].features["union"])
        self.assertTrue(self.by_name["Bits"].features["bitfield"])
        self.assertTrue(self.by_name["jump"].features["goto"])
        self.assertTrue(self.by_name["varargs"].features["variadic"])
        self.assertTrue(self.by_name["varargs"].features["va_list"])
        self.assertTrue(self.by_name["static_state"].features["static_local"])
        self.assertTrue(self.by_name["conditional"].features["conditional_compilation"])

    def test_classification_and_reason_selection(self) -> None:
        self.assertEqual(self.by_name["simple"].bucket, Bucket.TRIVIAL)
        self.assertEqual(self.by_name["pointer_ok"].bucket, Bucket.TRIVIAL)
        self.assertEqual(self.by_name["pointer_math"].bucket, Bucket.REFACTOR_THEN_DSL)
        self.assertEqual(self.by_name["pointer_math"].primary_reason, "pointer_arithmetic")
        self.assertEqual(self.by_name["callback"].bucket, Bucket.NEEDS_TRANSPILER)
        self.assertEqual(self.by_name["varargs"].primary_reason, "variadic")
        self.assertEqual(self.by_name["Value"].bucket, Bucket.NEEDS_TRANSPILER)

    def test_structural_declarations_and_unknown_fallback(self) -> None:
        self.assertIn("Packet", self.by_name)
        self.assertTrue(self.by_name["Packet"].features["flexible_array"])
        self.assertIn("global_value", self.by_name)
        self.assertTrue(self.by_name["global_value"].features["mutable_global"])
        self.assertTrue(self.by_name["use_global"].features["global_write"])
        self.assertTrue(self.by_name["use_global"].features["global_read"])
        self.assertIn("Count", self.by_name)
        self.assertIn("Color", self.by_name)
        bucket, reason, _, confidence = classify({"macro_generated_declaration": True})
        self.assertEqual((bucket, reason, confidence), (Bucket.UNKNOWN, "macro_generated_declaration", "low"))

    def test_sampling_is_deterministic_and_blank_for_humans(self) -> None:
        first, second = sample(self.records, 6423), sample(self.records, 6423)
        self.assertEqual(first, second)
        self.assertEqual(first["inventory_methodology_version"], INVENTORY_METHODOLOGY_VERSION)
        for bucket in first["buckets"]:
            self.assertLessEqual(bucket["actual_count"], bucket["requested_count"])
            for record in bucket["declarations"]:
                self.assertEqual(record["human_bucket"], "")
                self.assertEqual(record["human_notes"], "")
                self.assertEqual(record["agreement"], "")

    def test_serialization_and_summary(self) -> None:
        output = self.root / "out"
        write_outputs(self.records, output, application="synthetic", application_commit="abc123", seed=7)
        payload = json.loads((output / "inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["inventory_methodology_version"], 1)
        with (output / "inventory.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), len(self.records))
            self.assertTrue(all(row["inventory_methodology_version"] == "1" for row in rows))
        summary = (output / "summary.md").read_text(encoding="utf-8")
        self.assertIn("Bucket", summary)
        self.assertIn("UNKNOWN declarations", summary)


if __name__ == "__main__":
    unittest.main()
