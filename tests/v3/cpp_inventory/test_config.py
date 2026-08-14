from pathlib import Path
import tempfile
import unittest

from v3.cpp_inventory.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_and_resolves_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "sample.toml"
            config.write_text(
                'project = "sample"\nrepo_path = "repo"\ncompile_commands_path = "repo/compile_commands.json"\ninclude_paths = ["repo/include"]\nexclude_paths = ["repo/tests"]\n'
            )
            loaded = load_config(config)
            self.assertEqual(loaded.project, "sample")
            self.assertEqual(loaded.repo_path, root / "repo")
            self.assertEqual(loaded.include_paths, (root / "repo/include",))
