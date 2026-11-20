"""Public smoke tests for Section B. Run:  python -m pytest tests -q

The whole team runs on a RoutedLLM: one script per role, picked by how the role's system prompt starts.
"""
from pathlib import Path

import pytest

import submission_adapter as S
from pa4 import team as T
from pa4.llm import RoutedLLM, reply
from pa4.tasks import fresh_copy

FIXTURES = Path(__file__).parent / "fixtures"
FIX_OLD = "    if n % 2 == 0:\n        return s[mid]"
FIX_NEW = "    if n % 2 == 0:\n        return (s[mid - 1] + s[mid]) / 2"
SUP, CODER, TESTER = T.SUPERVISOR_PROMPT, T.CODER_PROMPT, T.TESTER_PROMPT


def handoff(to, instructions=""):
    return reply(tool_calls=[("handoff", {"to": to, "instructions": instructions})])


@pytest.fixture
def task(tmp_path):
    return fresh_copy(FIXTURES, "median", tmp_path / "median")


def test_team_happy_path(task):
    llm = RoutedLLM({
        SUP: [handoff("coder", "Average the two middle values for even n."), handoff("tester"), handoff("finish")],
        CODER: [reply(tool_calls=[("edit_file", {"path": "src/stats.py", "old_str": FIX_OLD, "new_str": FIX_NEW})]),
                reply(tool_calls=[("run_tests", {})]), reply("Fixed the even branch.")],
        TESTER: [reply(tool_calls=[("run_tests", {})]), reply("VERDICT: PASS\nAll tests pass.")],
    })
    r = S.run_team(task, llm, S.TeamConfig())
    assert r["solved"] and r["status"] == "done"
    assert r["handoffs"] == ["coder", "tester", "finish"] and r["rounds"] == 3
    assert r["prompt_tokens"] == 800 and r["completion_tokens"] == 160


def test_pass_at_k_and_pass_hat_k():
    assert S.pass_at_k(10, 3, 1) == pytest.approx(0.3)
    assert S.pass_hat_k(4, 2, 2) == pytest.approx(1 / 6)


def test_needs_approval():
    assert S.needs_approval("run_shell", {"command": "ls"})
    assert not S.needs_approval("edit_file", {"path": "src/app.py"})
    assert S.needs_approval("edit_file", {"path": "ISSUE.md"})
