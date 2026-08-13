from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rust_baseline.config import ConfigError, load_config
from rust_baseline.report import create_experiment_id
from rust_baseline.source_scan import iter_production_rust_files, scan_rust_file, scan_source_tree, strip_non_code


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "rust_baseline" / "sample_crate"


class RustBaselineScannerTests(unittest.TestCase):
    def test_strip_non_code_ignores_comments_and_strings(self) -> None:
        path = FIXTURE_ROOT / "src" / "lib.rs"
        stripped = strip_non_code(path.read_text(encoding="utf-8"))
        self.assertNotIn("unsafe in comment", stripped)
        self.assertNotIn("unsafe in string", stripped)
        self.assertIn("unsafe fn declared_unsafe", stripped)

    def test_iter_production_files_excludes_tests_and_examples(self) -> None:
        files = [path.relative_to(FIXTURE_ROOT).as_posix() for path in iter_production_rust_files(FIXTURE_ROOT)]
        self.assertEqual(files, ["src/extra.rs", "src/lib.rs"])

    def test_scan_source_tree_collects_expected_metrics(self) -> None:
        result = scan_source_tree(FIXTURE_ROOT)
        metrics = result["metrics"]
        self.assertEqual(metrics["production_files"], 2)
        self.assertEqual(metrics["functions_total"], 10)
        self.assertEqual(metrics["functions_unsafe_declared"], 1)
        self.assertEqual(metrics["functions_with_unsafe"], 3)
        self.assertEqual(metrics["functions_with_any_explicit_unsafe"], 4)
        self.assertEqual(metrics["functions_without_explicit_unsafe"], 6)
        self.assertEqual(metrics["unsafe_trait_count"], 1)
        self.assertEqual(metrics["unsafe_impl_count"], 1)
        self.assertEqual(metrics["unsafe_block_count"], 5)
        self.assertEqual(metrics["files_with_unsafe"], 1)
        self.assertEqual(metrics["unsafe_loc_estimate"], 18)
        self.assertAlmostEqual(metrics["safe_function_pct"], 90.0)
        self.assertAlmostEqual(metrics["functions_without_explicit_unsafe_pct"], 60.0)
        self.assertEqual(result["top_unsafe_files"][0]["path"], "src/lib.rs")
        self.assertEqual(result["unsafe_counts_per_file"]["src/lib.rs"]["unsafe_block_count"], 5)

    def test_declared_unsafe_with_unsafe_block_counts_once_in_union(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "both.rs"
            path.write_text(
                "pub unsafe fn both() {\n    unsafe {\n        helper();\n    }\n}\n\nfn helper() {}\n",
                encoding="utf-8",
            )
            summary = scan_rust_file(root, path).to_dict()
        self.assertEqual(summary["functions_total"], 2)
        self.assertEqual(summary["functions_unsafe_declared"], 1)
        self.assertEqual(summary["functions_with_unsafe"], 1)
        self.assertEqual(summary["functions_with_any_explicit_unsafe"], 1)
        self.assertEqual(summary["functions_without_explicit_unsafe"], 1)


class RustBaselineConfigTests(unittest.TestCase):
    def test_loads_exact_version_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            path.write_text(
                'workspace_root = ".cache"\nresults_root = "results"\n\n[[crate]]\nname = "demo"\npackage = "demo"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )
            config = load_config(path)
        self.assertEqual(config.crates[0].version, "1.2.3")
        self.assertTrue(str(config.workspace_root).endswith(".cache"))

    def test_rejects_unpinned_repo_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            path.write_text(
                '[[crate]]\nname = "demo"\npackage = "demo"\nrepo = "https://example.com/demo.git"\n',
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_rejects_placeholder_pin(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            path.write_text(
                '[[crate]]\nname = "demo"\npackage = "demo"\nrepo = "https://example.com/demo.git"\nrev = "<PINNED COMMIT>"\n',
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(path)


class RustBaselineReportTests(unittest.TestCase):
    def test_experiment_id_is_timestamped(self) -> None:
        experiment_id = create_experiment_id()
        self.assertTrue(experiment_id.startswith("baseline-"))
        self.assertGreater(len(experiment_id), len("baseline-2026"))

    def test_fixture_source_scan_is_json_serializable(self) -> None:
        payload = scan_source_tree(FIXTURE_ROOT)
        encoded = json.dumps(payload, sort_keys=True)
        self.assertIn("unsafe_loc_estimate_basis", encoded)
