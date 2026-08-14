from pathlib import Path
import tempfile
import unittest

from v3.cpp_inventory.cli import run_scan


class CliTests(unittest.TestCase):
    def test_scan_writes_v3_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "sample.toml"
            config.write_text('project = "sample"\nrepo_path = "."\ncompile_commands_path = "compile_commands.json"\n')
            output = run_scan(config, run_id="fixed", repository_root=root)
            self.assertEqual(output, root / "results/v3/cpp-inventory/sample/fixed")
            for name in ("manifest.json", "coverage.json", "functions.jsonl", "parse_failures.jsonl", "summary.json", "report.md"):
                self.assertTrue((output / name).is_file())
