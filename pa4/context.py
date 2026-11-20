"""Context engineering (A3). YOURS, except count_tokens.

An agent's context grows with every tool result. Two defences:
- truncate_output: keep any single tool result from flooding the context;
- compact_history: when the whole conversation gets too long, replace the middle with a short note.

The hidden tests check the exact rules in the docstrings.
"""
from __future__ import annotations

COMPACT_PREFIX = "[Earlier conversation compacted:"


def count_tokens(messages: list[dict]) -> int:
    """PROVIDED. Rough token count: 4 per message, plus 1 per 4 characters of content and of tool-call names
    and arguments. Deterministic and tokenizer-free; good enough for budgeting."""
    total = 0
    for m in messages:
        total += 4
        if isinstance(m.get("content"), str):
            total += len(m["content"]) // 4
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function", {})
            total += len(fn.get("name", "")) // 4 + len(fn.get("arguments") or "") // 4
    return total


def truncate_output(text: str, max_chars: int = 4000) -> str:
    """Shorten a tool result for the model.

    If len(text) <= max_chars, return it unchanged. Otherwise keep the first max_chars // 2 and the last
    max_chars // 2 characters, joined by the marker f"\\n[... {k} characters omitted ...]\\n", where k is the
    number of characters dropped. (Head and tail both matter: errors are often at the end.)
    """
    raise NotImplementedError("TODO A3: truncate_output")


def compact_history(messages: list[dict], max_tokens: int, count_fn=count_tokens) -> list[dict]:
    """Shrink a conversation to fit max_tokens (as measured by count_fn). Never mutates the input.

    - If count_fn(messages) <= max_tokens, return a new list with the same messages.
    - Otherwise the result is: head + [note] + tail.
      * head: the leading system message(s) plus the first user message (the task). Always kept.
      * tail: the shortest-to-drop suffix of the remaining messages, i.e. start the tail as EARLY as possible
        such that the whole result fits in max_tokens, under one constraint: the tail must not start with a
        'tool' message (a tool result without the assistant message that asked for it is rejected by the
        API). If no start fits, use the latest allowed start, so the last message is always kept.
      * note: one {"role": "user"} message replacing everything dropped. Its content starts with
        COMPACT_PREFIX, says how many messages were removed (f"{k} messages removed"), and lists the tools
        called in them with counts (f"tools used: view_file x3, run_tests x1"). If a run_tests result was
        dropped, it also includes the first line of the latest one (f"last test result: {line}").
    """
    raise NotImplementedError("TODO A3: compact_history")
