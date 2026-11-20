"""Submission adapter: the ONLY entry points the hidden tests use.

Do not change the names or signatures below. Each function forwards to your code in pa4/; if you restructure
pa4/, update the bodies here so the forwarding still works.
"""
from __future__ import annotations

from pa4 import agent, context, mcp_server, tools

# ----------------------------------------------------------------------------------------------------------
# Section A
# ----------------------------------------------------------------------------------------------------------


# A1 ------------------------------------------------------------------------------------------------------
def parse_tool_calls(message: dict) -> list[dict]:
    return agent.parse_tool_calls(message)


def run_agent(task_dir, llm_fn, tools=None, max_steps: int = 30, max_tokens: int = 300_000, verify: bool = True,
              max_nudges: int = 3, compact_at: int | None = 16_000, max_tool_chars: int = 4000) -> dict:
    return agent.run_agent(task_dir, llm_fn, tools=tools, max_steps=max_steps, max_tokens=max_tokens,
                           verify=verify, max_nudges=max_nudges, compact_at=compact_at,
                           max_tool_chars=max_tool_chars)


# A2 ------------------------------------------------------------------------------------------------------
def build_mcp_server(task_dir):
    return mcp_server.build_mcp_server(task_dir)


def mcp_tools_to_openai(mcp_tools) -> list[dict]:
    return mcp_server.mcp_tools_to_openai(mcp_tools)


def call_result_to_text(result) -> str:
    return mcp_server.call_result_to_text(result)


# A3 ------------------------------------------------------------------------------------------------------
def view_file(task_dir, path: str, start: int = 1, window: int = 60) -> str:
    return tools.view_file(task_dir, path, start, window)


def search_code(task_dir, pattern: str, max_hits: int = 30) -> str:
    return tools.search_code(task_dir, pattern, max_hits)


def edit_file(task_dir, path: str, old_str: str, new_str: str) -> str:
    return tools.edit_file(task_dir, path, old_str, new_str)


def edit_lines(task_dir, path: str, start: int, end: int, new_text: str) -> str:
    return tools.edit_lines(task_dir, path, start, end, new_text)


def tool_specs() -> list[dict]:
    return tools.TOOL_SPECS


def truncate_output(text: str, max_chars: int = 4000) -> str:
    return context.truncate_output(text, max_chars)


def compact_history(messages: list[dict], max_tokens: int, count_fn=None) -> list[dict]:
    return context.compact_history(messages, max_tokens, count_fn or context.count_tokens)


# ----------------------------------------------------------------------------------------------------------
# Section B
# ----------------------------------------------------------------------------------------------------------
from pa4 import eval as evaluation  # noqa: E402  (eval would shadow the builtin)
from pa4 import team  # noqa: E402

TeamConfig = team.TeamConfig


# B1 ------------------------------------------------------------------------------------------------------
def build_team_graph(llm_fn, cfg=None, checkpointer=None):
    return team.build_team_graph(llm_fn, cfg, checkpointer)


def run_team(task_dir, llm_fn, cfg=None, thread_id: str = "run-0", checkpointer=None, approver=None) -> dict:
    kwargs = {} if approver is None else {"approver": approver}
    return team.run_team(task_dir, llm_fn, cfg, thread_id=thread_id, checkpointer=checkpointer, **kwargs)


# B2 ------------------------------------------------------------------------------------------------------
def pass_at_k(n: int, c: int, k: int) -> float:
    return evaluation.pass_at_k(n, c, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    return evaluation.pass_hat_k(n, c, k)


def bootstrap_ci(results: dict, metric, k: int, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0):
    return evaluation.bootstrap_ci(results, metric, k, n_boot, alpha, seed)


def paired_comparison(a: dict, b: dict) -> dict:
    return evaluation.paired_comparison(a, b)


def matched_budget_solo(task_root, task: str, llm_fn, token_budget: int, work_dir, **agent_kwargs) -> dict:
    return evaluation.matched_budget_solo(task_root, task, llm_fn, token_budget, work_dir, **agent_kwargs)


# B3 ------------------------------------------------------------------------------------------------------
def needs_approval(name: str, args: dict) -> bool:
    return team.needs_approval(name, args)


def gated_toolbox(inner):
    return team.GatedToolBox(inner)


def coder_tools(task_dir, cfg):
    return team.coder_tools(task_dir, cfg)
