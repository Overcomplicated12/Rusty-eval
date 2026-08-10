from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from harness.workspace import GitWorktree


def git(directory: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(directory), *args], text=True, capture_output=True, check=True)
    return completed.stdout


class GitWorktreeTests(unittest.TestCase):
    def test_create_diff_and_cleanup_in_a_temporary_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Harness test")
            (repo / "source.cpp").write_text("int value = 1;\n", encoding="utf-8")
            git(repo, "add", "source.cpp")
            git(repo, "commit", "-m", "initial")
            commit = git(repo, "rev-parse", "HEAD").strip()
            tree = GitWorktree(repo, root / "worktree", commit)
            tree.create()
            self.assertEqual(git(tree.path, "rev-parse", "HEAD").strip(), commit)
            (tree.path / "source.cpp").write_text("int value = 2;\n", encoding="utf-8")
            self.assertEqual(tree.changed_files(), ["source.cpp"])
            patch = tree.save_diff(root / "result" / "change.diff")
            self.assertIn("value = 2", patch.read_text(encoding="utf-8"))
            tree.cleanup(force=True)
            self.assertFalse(tree.path.exists())
            self.assertEqual(git(repo, "status", "--porcelain"), "")
