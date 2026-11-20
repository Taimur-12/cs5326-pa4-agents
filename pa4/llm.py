"""Talking to a model. PROVIDED.

Everything in this PA calls the model through an **LLMFn**:

    llm_fn(messages, tools) -> {
        "content": str | None,           # text the model wrote (may be empty when it calls tools)
        "tool_calls": [                  # possibly empty
            {"id": str, "name": str, "arguments": str},   # arguments: the RAW JSON string the model produced
        ],
        "finish_reason": str,            # "stop", "tool_calls", "length", ...
        "usage": {"prompt_tokens": int, "completion_tokens": int},
    }

`messages` and `tools` use the OpenAI chat-completions format. Because the agent only ever sees an LLMFn,
the same code runs against vLLM on Kaggle, any OpenAI-compatible API, or a scripted fake in the tests.

`arguments` is deliberately the raw string: models sometimes emit invalid JSON, and handling that is your job (A1).
"""
from __future__ import annotations

import json
from typing import Callable, Iterable

LLMFn = Callable[[list, list], dict]


def openai_llm_fn(base_url: str = "http://localhost:8000/v1", model: str = "qwen3.5-9b",
                  temperature: float = 0.7, max_tokens: int = 4096, timeout: float = 1800,
                  enable_thinking: bool = False, api_key: str = "EMPTY") -> LLMFn:
    """An LLMFn backed by an OpenAI-compatible server (the vLLM server on Kaggle by default).

    timeout is per request. It is long on purpose: on a busy T4 one long reply can take many minutes,
    and a request that times out ends the attempt (a 600 s timeout is too short).
    The client is thread-safe, so one LLMFn can be shared by attempts running in parallel threads.
    """
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout, max_retries=1)
    extra = {"chat_template_kwargs": {"enable_thinking": enable_thinking}}

    def llm_fn(messages: list, tools: list) -> dict:
        r = client.chat.completions.create(model=model, messages=messages, tools=tools or None,
                                           temperature=temperature, max_tokens=max_tokens, extra_body=extra)
        choice = r.choices[0]
        m = choice.message
        return {
            "content": m.content,
            "tool_calls": [{"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments or ""}
                           for tc in (m.tool_calls or [])],
            "finish_reason": choice.finish_reason,
            "usage": {"prompt_tokens": r.usage.prompt_tokens if r.usage else 0,
                      "completion_tokens": r.usage.completion_tokens if r.usage else 0},
        }

    return llm_fn


def reply(content: str | None = None, tool_calls: Iterable = (), finish_reason: str | None = None,
          prompt_tokens: int = 100, completion_tokens: int = 20) -> dict:
    """Build one LLMFn response by hand. tool_calls items are (name, args) pairs; args may be a dict
    (serialised for you) or a raw string (sent as-is, e.g. to fake invalid JSON)."""
    calls = []
    for i, (name, args) in enumerate(tool_calls):
        calls.append({"id": f"call_{i}_{name}", "name": name,
                      "arguments": args if isinstance(args, str) else json.dumps(args)})
    return {"content": content, "tool_calls": calls,
            "finish_reason": finish_reason or ("tool_calls" if calls else "stop"),
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}}


class ScriptedLLM:
    """A fake LLMFn for offline testing. Give it a list of replies (see `reply`), or a function
    f(messages, tools) -> reply. With a list, the last reply repeats once the script runs out.

    It records every request in .requests so tests can inspect what the agent sent.
    """

    def __init__(self, script):
        self.script = script
        self.requests: list[tuple[list, list]] = []

    def __call__(self, messages: list, tools: list) -> dict:
        self.requests.append((json.loads(json.dumps(messages)), tools))
        if callable(self.script):
            return self.script(messages, tools)
        i = min(len(self.requests) - 1, len(self.script) - 1)
        return json.loads(json.dumps(self.script[i]))


class RoutedLLM:
    """A fake LLMFn for teams: one ScriptedLLM per role, picked by how the system prompt starts.

        llm = RoutedLLM({"You are the supervisor": [...], "You are the Coder": [...], "You are the Tester": [...]})

    Each role's script advances independently. llm.routes[prefix].requests shows what that role was sent;
    llm.calls counts calls per prefix. A system prompt matching no prefix raises KeyError.
    """

    def __init__(self, routes: dict):
        self.routes = {prefix: s if isinstance(s, ScriptedLLM) else ScriptedLLM(s) for prefix, s in routes.items()}

    @property
    def calls(self) -> dict:
        return {p: len(s.requests) for p, s in self.routes.items()}

    def __call__(self, messages: list, tools: list) -> dict:
        system = messages[0].get("content", "") if messages and messages[0].get("role") == "system" else ""
        for prefix, scripted in self.routes.items():
            if system.startswith(prefix):
                return scripted(messages, tools)
        raise KeyError(f"no scripted role for a system prompt starting {system[:40]!r}")
