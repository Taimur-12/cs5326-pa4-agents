"""Public smoke tests for Section A. Run:  python -m pytest tests -q

These check the basics only. The hidden tests check every rule in the docstrings.
Everything here is offline: the "model" is a ScriptedLLM.
"""
from pathlib import Path

import pytest

import submission_adapter as S
from pa4.llm import ScriptedLLM, reply
from pa4.tasks import fresh_copy, is_solved

FIXTURES = Path(__file__).parent / "fixtures"
FIX_OLD = "    if n % 2 == 0:\n        return s[mid]"
FIX_NEW = "    if n % 2 == 0:\n        return (s[mid - 1] + s[mid]) / 2"


@pytest.fixture
def task(tmp_path):
    return fresh_copy(FIXTURES, "median", tmp_path / "median")


# A1 -------------------------------------------------------------------------------------------------------
def test_parse_tool_calls():
    calls = S.parse_tool_calls(reply(tool_calls=[("view_file", {"path": "a.py"}), ("run_tests", "{oops")]))
    assert calls[0]["name"] == "view_file" and calls[0]["args"] == {"path": "a.py"} and calls[0]["error"] is None
    assert calls[1]["args"] is None and calls[1]["error"].startswith("arguments were not valid JSON")


def test_agent_fixes_the_fixture(task):
    llm = ScriptedLLM([
        reply(tool_calls=[("view_file", {"path": "src/stats.py"})]),
        reply(tool_calls=[("edit_file", {"path": "src/stats.py", "old_str": FIX_OLD, "new_str": FIX_NEW})]),
        reply(tool_calls=[("run_tests", {})]),
        reply("Fixed median for even-length lists."),
    ])
    r = S.run_agent(task, llm)
    assert r["solved"] and r["stop"] == "final_answer"
    assert r["steps"] == 4 and r["tool_calls"] == 3 and r["prompt_tokens"] == 400
    assert [m["role"] for m in r["messages"]][:3] == ["system", "user", "assistant"]


def test_claiming_done_without_testing_is_nudged(task):
    llm = ScriptedLLM([reply("I think it is fixed.")])
    r = S.run_agent(task, llm, max_nudges=2)
    assert r["stop"] == "stopped_after_nudges" and r["nudges"] == 2 and not r["solved"]


# A2 -------------------------------------------------------------------------------------------------------
def test_mcp_server_serves_the_tools(task):
    from pa4.mcp_bridge import MCPToolBox

    with MCPToolBox(S.build_mcp_server(task)) as tb:
        assert sorted(tb.names) == ["edit_file", "edit_lines", "list_files", "run_tests", "search_code", "view_file"]
        assert "src/stats.py" in tb.call("list_files", {})
        assert tb.call("view_file", {"path": "tests/test_stats.py"}).startswith("ERROR")


# A3 -------------------------------------------------------------------------------------------------------
def test_view_and_edit(task):
    out = S.view_file(task, "src/stats.py", start=1, window=3)
    assert out.splitlines()[0] == "src/stats.py (lines 1-3 of 8)"
    assert out.splitlines()[1] == "   1 | def median(xs):"
    assert S.edit_file(task, "src/stats.py", FIX_OLD, FIX_NEW) == "OK: edited src/stats.py"
    assert is_solved(task)


def test_tool_specs_cover_every_tool():
    names = {s["function"]["name"] for s in S.tool_specs()}
    assert names == {"list_files", "view_file", "search_code", "edit_file", "edit_lines", "run_tests"}


def test_truncate_output():
    out = S.truncate_output("a" * 50 + "b" * 50, max_chars=20)
    assert out.startswith("a" * 10) and out.endswith("b" * 10) and "80 characters omitted" in out
