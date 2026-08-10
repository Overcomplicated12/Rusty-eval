"""Isolated git worktree management that never resets a canonical checkout."""

from __future__ import annotations

import subprocess
from pathlib import Path


class WorkspaceError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if completed.returncode:
        raise WorkspaceError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout


class GitWorktree:
    """A disposable detached worktree associated with a pinned source commit."""

    def __init__(self, canonical_repo: str | Path, path: str | Path, commit: str) -> None:
        self.canonical_repo = Path(canonical_repo).resolve()
        self.path = Path(path).resolve()
        self.commit = commit

    def create(self) -> Path:
        if self.path.exists():
            raise WorkspaceError(f"refusing to reuse existing worktree path: {self.path}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _git(self.canonical_repo, "worktree", "add", "--detach", str(self.path), self.commit)
        self.verify_commit()
        return self.path

    def verify_commit(self) -> None:
        actual = _git(self.path, "rev-parse", "HEAD").strip()
        expected = _git(self.canonical_repo, "rev-parse", self.commit).strip()
        if actual != expected:
            raise WorkspaceError(f"worktree commit mismatch: expected {expected}, found {actual}")

    def changed_files(self) -> list[str]:
        status = _git(self.path, "status", "--porcelain")
        return sorted({line[3:] for line in status.splitlines() if len(line) >= 4})

    def diff(self) -> str:
        return _git(self.path, "diff", "--binary", "HEAD")

    def save_diff(self, destination: str | Path) -> Path:
        output = Path(destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.diff(), encoding="utf-8")
        return output

    def cleanup(self, *, force: bool = False) -> None:
        """Remove this worktree without ever resetting the canonical checkout.

        A dirty worktree is retained by default so callers can preserve its diff
        as an experiment artifact before explicitly discarding it.
        """
        if self.path.exists():
            arguments = ["worktree", "remove"]
            if force:
                arguments.append("--force")
            arguments.append(str(self.path))
            _git(self.canonical_repo, *arguments)
