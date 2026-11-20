"""The agent's tools (A2, A3). Partly PROVIDED, partly YOURS.

Every tool is a plain function whose first argument is the task directory; the rest are what the model
supplies. Tools return a string for the model. On bad input they raise `ToolError` with a message written
for the model (the tool box turns it into "ERROR: <message>"), so the model can correct itself.

The precise behaviour of each TODO is in its docstring; the hidden tests check exactly that.
"""
from __future__ import annotations

import py_compile
from pathlib import Path

from .tasks import ToolError, resolve_path, run_test_suite, visible_files

VIEW_DEFAULT = 60   # default window of view_file
VIEW_MAX = 200      # largest window view_file will show


# ---------------------------------------------------------------------------------------------------------
# PROVIDED tools
# ---------------------------------------------------------------------------------------------------------
def list_files(task_dir) -> str:
    """Every file the agent may see, one repo-relative path per line."""
    return "\n".join(visible_files(task_dir))


def run_tests(task_dir) -> str:
    """Run the hidden test suite: 'passed: P, failed: F, errors: E' plus short failure lines."""
    return run_test_suite(task_dir).summary()


# ---------------------------------------------------------------------------------------------------------
# YOUR tools (A3: designed for an LLM, not for a human)
# ---------------------------------------------------------------------------------------------------------
def _read_text(task_dir, path) -> tuple[Path, str]:
    p = resolve_path(task_dir, path)
    if not p.is_file():
        raise ToolError(f"no such file: {path}")
    return p, p.read_text(encoding="utf-8")


def view_file(task_dir, path: str, start: int = 1, window: int = VIEW_DEFAULT) -> str:
    """Show a window of a file with line numbers.

    Output: a header line '{path} (lines {a}-{b} of {n})', then one line per file line formatted
    f"{i:>4} | {text}". `start` is clamped into [1, n] and `window` into [1, VIEW_MAX]. An empty file gives
    exactly '{path} (empty file)'. A missing path or a directory raises ToolError('no such file: {path}').
    """
    raise NotImplementedError("TODO A3: view_file")


def search_code(task_dir, pattern: str, max_hits: int = 30) -> str:
    """Find lines containing `pattern` (plain substring, case-sensitive) in the visible files.

    One hit per line, 'path:line: text', with text stripped and cut to 200 characters, ordered by path then
    line number. At most max_hits hit lines; if there are more, add a final line '[... N more matches]'.
    No hits gives exactly f"no matches for {pattern!r}". An empty pattern raises ToolError. Files that are
    not valid UTF-8 are skipped.
    """
    raise NotImplementedError("TODO A3: search_code")


def edit_file(task_dir, path: str, old_str: str, new_str: str) -> str:
    """Replace the single occurrence of old_str in a file with new_str.

    old_str must occur exactly once; otherwise raise ToolError(f"old_str must match exactly once, found {k}
    matches") and leave the file alone (an empty old_str counts as 0 matches). For a .py file, if the result
    does not compile, restore the original and raise ToolError whose message starts with
    'edit reverted: syntax error' and contains f"line {n}", n being the line of the error (for example
    'edit reverted: syntax error at line 5: invalid syntax'). On success return f"OK: edited {path}".
    A missing file raises ToolError('no such file: {path}').
    """
    raise NotImplementedError("TODO A3: edit_file")


def edit_lines(task_dir, path: str, start: int, end: int, new_text: str) -> str:
    """Replace lines start..end (1-based, inclusive) with new_text.

    new_text may hold any number of lines; '' deletes the range. end == start - 1 inserts before line
    `start` without removing anything. Valid ranges: 1 <= start <= n + 1 and start - 1 <= end <= n
    (n = number of lines); anything else raises ToolError and leaves the file alone. A trailing newline is
    added to new_text if it lacks one (unless it is ''). Same syntax check and revert as edit_file. On
    success return f"OK: replaced lines {start}-{end} of {path} ({k} new lines)", k = lines in new_text.
    """
    raise NotImplementedError("TODO A3: edit_lines")


# ---------------------------------------------------------------------------------------------------------
# Tool specs (OpenAI function-calling format). Two are PROVIDED; the other four are YOURS (A3).
# ---------------------------------------------------------------------------------------------------------
def _spec(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required}}}


LIST_FILES_SPEC = _spec("list_files", "List every file in the repository you can see (tests are hidden).", {}, [])
RUN_TESTS_SPEC = _spec("run_tests", "Run the hidden test suite. Returns pass/fail counts and short failure "
                       "lines. Run it after every change.", {}, [])

TOOL_SPECS = [
    LIST_FILES_SPEC,
    # TODO A3: add specs for view_file, search_code, edit_file and edit_lines (use _spec). Parameter names
    # must match the function arguments after task_dir; mark the ones without defaults as required.
    # Descriptions matter: they are the only manual the model gets.
    RUN_TESTS_SPEC,
]

TOOL_FUNCTIONS = {"list_files": list_files, "view_file": view_file, "search_code": search_code,
                  "edit_file": edit_file, "edit_lines": edit_lines, "run_tests": run_tests}


# ---------------------------------------------------------------------------------------------------------
# PROVIDED: naive tools for the A3 interface ablation (what a human-style API looks like to an LLM)
# ---------------------------------------------------------------------------------------------------------
def read_file(task_dir, path: str) -> str:
    """Return the whole file, no line numbers."""
    return _read_text(task_dir, path)[1]


def write_file(task_dir, path: str, content: str) -> str:
    """Overwrite an existing file completely. No syntax check. It never creates files: a new file such as a
    conftest.py could change how the hidden tests run."""
    p = resolve_path(task_dir, path)
    if not p.is_file():
        raise ToolError(f"no such file: {path}")
    p.write_text(content, encoding="utf-8")
    return f"OK: wrote {path}"


NAIVE_SPECS = [
    LIST_FILES_SPEC,
    _spec("read_file", "Read a whole file.", {"path": {"type": "string"}}, ["path"]),
    _spec("write_file", "Overwrite an existing file with new content.", {"path": {"type": "string"},
                                                               "content": {"type": "string"}}, ["path", "content"]),
    RUN_TESTS_SPEC,
]
NAIVE_FUNCTIONS = {"list_files": list_files, "read_file": read_file, "write_file": write_file,
                   "run_tests": run_tests}


# ---------------------------------------------------------------------------------------------------------
# PROVIDED: a tool box binds tools to one task directory
# ---------------------------------------------------------------------------------------------------------
class LocalToolBox:
    """Tools for one task, called in-process. `specs` go to the model; `call` runs one tool.

    call() returns the tool's string, or "ERROR: <message>" for a ToolError or bad arguments. Any other
    exception propagates: your agent loop must catch it (A1).
    """

    def __init__(self, task_dir, specs: list | None = None, functions: dict | None = None):
        self.task_dir = Path(task_dir)
        self.specs = TOOL_SPECS if specs is None else specs
        self.functions = TOOL_FUNCTIONS if functions is None else functions

    @property
    def names(self) -> list[str]:
        return [s["function"]["name"] for s in self.specs]

    def call(self, name: str, args: dict) -> str:
        fn = self.functions[name]
        try:
            return fn(self.task_dir, **args)
        except ToolError as e:
            return f"ERROR: {e}"
        except TypeError as e:
            return f"ERROR: bad arguments for {name}: {e}"


def naive_toolbox(task_dir) -> LocalToolBox:
    return LocalToolBox(task_dir, NAIVE_SPECS, NAIVE_FUNCTIONS)
