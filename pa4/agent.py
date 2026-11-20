"""The from-scratch agent loop (A1, A4). YOURS.

No frameworks in this file: plain Python over an LLMFn (see llm.py). Section B reuses this agent as a worker.

The loop, in one paragraph: send the conversation and the tool specs to the model; if it asks for tools, run
each one and append the results; if it replies without a tool call, decide whether that really ends the
attempt (A4); repeat until a stop condition. Every number in the returned dict is something you will
aggregate later, so keep the bookkeeping exact.

You may reword the prompt and the nudges below.
"""
from __future__ import annotations

import json
from pathlib import Path

from .context import compact_history, count_tokens, truncate_output
from .llm import LLMFn
from .tasks import is_solved
from .tools import LocalToolBox
from .trace import null_tracer

SYSTEM_PROMPT = (
    "You are a software engineering agent fixing a bug in a small Python repository.\n"
    "Use the tools to read the code, make small targeted edits, and run the tests. You cannot read the tests; "
    "run_tests tells you what fails.\n"
    "Run the tests after every change. When all tests pass, reply with a one-line summary and no tool call."
)

NUDGE_UNVERIFIED = (
    "You have not finished: the tests are not passing yet, or you have changed the code since you last ran "
    "them. Do not just describe a plan. Continue by calling a tool.")
NUDGE_CUT_OFF = "Your last reply was cut off by the length limit before you called a tool. Be brief and call a tool now."

STOP_REASONS = ("final_answer", "max_steps", "token_budget", "stopped_after_nudges", "llm_error")


def parse_tool_calls(message: dict) -> list[dict]:
    """Decode the tool calls of one LLMFn response (A1).

    Returns one dict per entry of message["tool_calls"], in order:
        {"id": str, "name": str, "args": dict | None, "error": str | None}
    - args is the decoded JSON object, and error is None, when `arguments` is a JSON object. An empty or
      whitespace-only `arguments` string means no arguments: args = {}.
    - Otherwise args is None and error is a short message for the model that starts with
      "arguments were not valid JSON" (undecodable) or "arguments must be a JSON object" (valid JSON but
      not an object, e.g. a list).
    - A missing or empty id becomes f"call_{index}" (index in the list), so every tool result can refer back.
    A response with no "tool_calls" key, or None, gives [].
    """
    raise NotImplementedError("TODO A1: parse_tool_calls")


def run_agent(task_dir, llm_fn: LLMFn, tools=None, max_steps: int = 30, max_tokens: int = 300_000,
              verify: bool = True, max_nudges: int = 3, compact_at: int | None = 16_000,
              max_tool_chars: int = 4000, system_prompt: str = SYSTEM_PROMPT, user_extra: str = "",
              tracer=null_tracer) -> dict:
    """Run one attempt on the task in task_dir and return its record (A1, A4).

    Setup: messages = [system_prompt, user "Fix this issue.\\n\\n" + ISSUE.md], with "\\n\\n" + user_extra
    appended to that user message when user_extra is non-empty (Section B uses it to pass a worker its
    instructions). tools defaults to LocalToolBox(task_dir). A tool box has .specs (sent to the model) and
    .names, and .call(name, args) -> str.

    Each step (at most max_steps model calls):
    1. Stop with "token_budget" BEFORE calling the model if prompt_tokens + completion_tokens spent so far
       >= max_tokens.
    2. If compact_at is not None and count_tokens(messages) > compact_at, replace messages with
       compact_history(messages, compact_at). It is on by default: prompt tokens dominate the cost, because the
       whole conversation is re-sent at every step.
    3. Call llm_fn(messages, tools.specs). If it raises, stop with "llm_error". Add its usage to the totals.
    4. Append the assistant message in OpenAI format: {"role": "assistant", "content": content or "",
       "tool_calls": [{"id", "type": "function", "function": {"name", "arguments"}}]} (omit "tool_calls"
       when there are none). Keep the raw arguments string, even if invalid.
    5. If there are tool calls, answer EVERY one, in order, with {"role": "tool", "tool_call_id": id,
       "content": text}, where text is:
       - for arguments parse_tool_calls could not decode (args None, either error): "ERROR: " + the parse error
         (counts in malformed_calls and tool_errors)
       - for a name not in tools.names: "ERROR: unknown tool '<name>'. Available tools: a, b, ..."
       - otherwise tools.call(name, args), or "ERROR: <ExceptionType>: <message>" if it raises;
       then truncate_output(text, max_tool_chars). Every text starting with "ERROR" counts in tool_errors.
    6. If there are no tool calls, the model wants to stop:
       - verify=False: stop with "final_answer".
       - verify=True (A4): accept ("final_answer") only if the latest run_tests result in this attempt was
         green (passed > 0, failed 0, errors 0) and no edit tool (edit_file, edit_lines, write_file) has
         returned a result starting with "OK" since then. Track both as the loop runs: compaction can drop the
         messages that held them. Otherwise, if max_nudges nudges were already used, stop with
         "stopped_after_nudges"; else append {"role": "user", "content": NUDGE_CUT_OFF if
         finish_reason == "length" else NUDGE_UNVERIFIED}, count a nudge, and continue.
    After max_steps calls without stopping: "max_steps".

    Returns {"task" (the task directory's name), "solved" (is_solved(task_dir), checked once at the end), "stop"
    (one of STOP_REASONS), "steps" (model calls that returned; a call that raised does not count), "tool_calls"
    (every tool call the model asked for, malformed and unknown ones included), "malformed_calls", "tool_errors",
    "nudges", "prompt_tokens", "completion_tokens", "messages" (the final conversation)}. The record must be
    JSON-serialisable: plain strings, numbers, booleans, lists and dicts only.
    Emit tracer events as described in trace.py (they help you debug and are not graded).
    """
    raise NotImplementedError("TODO A1/A4: run_agent")
