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
                'project = "sample"\nrepo_path = "repo"\ncompile_commands_path = "repo/compile_commands.json"\n[scope]\ninclude = ["src/**"]\nexclude = ["src/generated/**"]\n'
            )
            loaded = load_config(config)
            self.assertEqual(loaded.project, "sample")
            self.assertEqual(loaded.repo_path, root / "repo")
            self.assertEqual(loaded.scope_include, ("src/**",))
            self.assertEqual(loaded.scope_exclude, ("src/generated/**",))
