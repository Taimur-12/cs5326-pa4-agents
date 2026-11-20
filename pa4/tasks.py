"""Task suite helpers. PROVIDED: do not edit (the graders use their own copy).

A task is a directory holding a small buggy Python repository:

    ISSUE.md      the bug report the agent is given
    src/          the code to fix
    docs/         (some tasks) a spec the fix must follow
    tests/        the pytest suite that decides "solved". HIDDEN from the agent.

The agent may read and edit anything except tests/, and it can only learn about the tests by running them
(pass/fail counts plus short failure lines).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HIDDEN_DIRS = {"tests"}
SKIP_DIRS = {"__pycache__", ".pytest_cache"}


class ToolError(Exception):
    """Bad input to a tool (missing file, path outside the repo, ...).

    Tools raise it; the tool box turns it into an "ERROR: ..." string for the model.
    """


def list_tasks(root: str | Path) -> list[str]:
    """Names of the tasks under root (directories that contain an ISSUE.md), sorted."""
    root = Path(root)
    return sorted(p.name for p in root.iterdir() if (p / "ISSUE.md").is_file())


def fresh_copy(root: str | Path, task: str, dest: str | Path) -> Path:
    """Copy a pristine task to dest (replacing anything there) and return dest. Agents only ever touch copies."""
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(Path(root) / task, dest, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    return dest


def resolve_path(task_dir: str | Path, rel: str) -> Path:
    """Resolve a repo-relative path for a tool, refusing paths outside the repo and inside hidden dirs."""
    root = Path(task_dir).resolve()
    if not isinstance(rel, str) or not rel.strip():
        raise ToolError("path must be a non-empty string")
    p = (root / rel).resolve()
    if p != root and root not in p.parents:
        raise ToolError(f"path escapes the repository: {rel}")
    if HIDDEN_DIRS & set(p.relative_to(root).parts):
        raise ToolError("tests are hidden from the agent")
    return p


def visible_files(task_dir: str | Path) -> list[str]:
    """Repo-relative paths of every file the agent may see, sorted, using '/' separators."""
    root = Path(task_dir).resolve()
    out = []
    for p in sorted(root.rglob("*")):
        parts = p.relative_to(root).parts
        if p.is_file() and not (HIDDEN_DIRS & set(parts)) and not (SKIP_DIRS & set(parts)) \
                and not p.name.startswith("."):
            out.append("/".join(parts))
    return out


@dataclass
class TestResult:
    passed: int
    failed: int
    errors: int
    output: str

    @property
    def ok(self) -> bool:
        """All tests passed (and there was at least one)."""
        return self.passed > 0 and self.failed == 0 and self.errors == 0

    def summary(self, max_lines: int = 12) -> str:
        """What the agent sees: 'passed: P, failed: F, errors: E' plus up to max_lines short failure lines."""
        head = f"passed: {self.passed}, failed: {self.failed}, errors: {self.errors}"
        if self.ok:
            return head
        lines = [l for l in self.output.splitlines()
                 if l.startswith(("E ", "FAILED", "ERROR")) or ".py:" in l][:max_lines]
        return "\n".join([head] + lines)


def run_test_suite(task_dir: str | Path, timeout: float = 60) -> TestResult:
    """Run the task's hidden pytest suite in a subprocess (with a timeout) and count the results."""
    root = Path(task_dir).resolve()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider", "tests"],
            cwd=root, capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL)  # never inherit stdin: under an MCP stdio server it is the protocol pipe
    except subprocess.TimeoutExpired:
        return TestResult(0, 0, 1, "ERROR: tests timed out (infinite loop or very slow code?)")
    out = (proc.stdout + proc.stderr).replace(str(root) + "\\", "").replace(str(root) + "/", "")

    def count(word: str) -> int:
        m = re.search(rf"(\d+) {word}", out)
        return int(m.group(1)) if m else 0

    return TestResult(count("passed"), count("failed"), count("error"), out)


def is_solved(task_dir: str | Path) -> bool:
    """The grading check: the hidden suite passes completely."""
    return run_test_suite(task_dir).ok
