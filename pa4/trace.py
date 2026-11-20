"""Structured traces. PROVIDED.

A tracer is any callable taking one event dict. `JsonlTracer` appends events to a JSONL file, one line each: pass
one as run_agent(..., tracer=...) to see what an attempt did while you debug. Traces are not submitted; the R6
failure audit reads the team transcripts that experiments.py saves.

Event shapes the reference agent emits (yours should emit at least these):
    {"type": "llm_call", "step": int, "prompt_tokens": int, "completion_tokens": int, "finish_reason": str}
    {"type": "tool_call", "step": int, "name": str, "ok": bool}
    {"type": "nudge", "step": int, "reason": str}
    {"type": "stop", "step": int, "stop": str}
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path


class JsonlTracer:
    def __init__(self, path: str | Path, **fields):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fields = fields  # added to every event, e.g. task="roman", attempt=0
        self._lock = threading.Lock()

    def __call__(self, event: dict) -> None:
        row = {"t": round(time.time(), 3), **self.fields, **event}
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")


def null_tracer(event: dict) -> None:
    """A tracer that does nothing."""
