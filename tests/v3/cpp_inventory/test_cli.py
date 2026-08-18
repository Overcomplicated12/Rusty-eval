import json
from pathlib import Path
import tempfile
import unittest

from v3.cpp_inventory.cli import run_scan
from v3.cpp_inventory.runner import select_translation_units


class CliTests(unittest.TestCase):
    def test_selects_directory_translation_units_and_collects_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            selected = source / "selected"
            selected.mkdir(parents=True)
            (selected / "good.cc").write_text("void good() {}\n", encoding="utf-8")
            (selected / "bad.cc").write_text("void bad() {}\n", encoding="utf-8")
            other = source / "other"
            other.mkdir()
            (other / "skip.cc").write_text("void skip() {}\n", encoding="utf-8")
            build = root / "build"
            build.mkdir()
            database = root / "compile_commands.json"
            database.write_text(
                json.dumps(
                    [
                        {"directory": str(build), "file": "../source/selected/good.cc", "command": "clang++ -c ../source/selected/good.cc"},
                        {"directory": str(build), "file": "../source/selected/bad.cc", "command": "clang++ -c ../source/selected/bad.cc"},
                        {"directory": str(build), "file": "../source/other/skip.cc", "command": "clang++ -c ../source/other/skip.cc"},
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                select_translation_units(database, selected),
                [selected / "good.cc", selected / "bad.cc"],
            )
            scanner = root / "clang_inventory"
            scanner.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, pathlib, sys\n"
                "arguments = dict(arg[2:].split('=', 1) for arg in sys.argv[1:])\n"
                "if arguments['source-file'].endswith('bad.cc'):\n"
                "    print('intentional scanner failure', file=sys.stderr)\n"
                "    raise SystemExit(7)\n"
                "pathlib.Path(arguments['output']).write_text(json.dumps({'translation_unit': arguments['source-file'], 'cwd': os.getcwd()}) + '\\n')\n",
                encoding="utf-8",
            )
            scanner.chmod(0o755)
            config = root / "sample.toml"
            config.write_text(
                'project = "sample"\nrepo_path = "."\ncompile_commands_path = "compile_commands.json"\n',
                encoding="utf-8",
            )
            output = run_scan(
                config,
                directory=selected,
                clang_inventory=scanner,
                run_id="fixed",
                repository_root=root,
            )
            self.assertEqual(output, root / "results/v3/cpp-inventory/sample/fixed")
            coverage = json.loads((output / "coverage.json").read_text(encoding="utf-8"))
            self.assertEqual(coverage["translation_units_parsed"], 1)
            self.assertEqual(coverage["translation_units_seen"], 2)
            self.assertEqual(coverage["primary_denominator"], 1)
            records = (output / "functions.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(records), 1)
            self.assertTrue(json.loads(records[0])["translation_unit"].endswith("good.cc"))
            failures = (output / "parse_failures.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(failures), 1)
            self.assertEqual(json.loads(failures[0])["returncode"], 7)
