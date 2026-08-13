from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from harness.config import ConfigError, load_config

VALID = '''workspace_root = ".worktrees"
[application]
name = "synthetic"
repo = "../synthetic"
commit = "abc123"
source_roots = ["src"]
[rustycpp]
repo = "../rusty-cpp"
commit = "def456"
command = ["rustycpp"]
[commands]
build = ["build"]
targeted_test = ["test", "targeted"]
[edit_policy]
allowed_files = ["src/**"]
'''


class ConfigTests(unittest.TestCase):
    def test_loads_valid_config_and_defaults_budgets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            path.write_text(VALID, encoding="utf-8")
            config = load_config(path)
        self.assertEqual(config.application_name, "synthetic")
        self.assertEqual(config.attempt_budgets.max_total_attempts, 7)
        self.assertEqual(config.edit_policy.allowed_files, ["src/**"])

    def test_rejects_missing_pinned_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            path.write_text(VALID.replace('commit = "abc123"\n', "", 1), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)
