"""Serving the model on Kaggle. PROVIDED.

    proc = start_server()            # ~10 minutes, once per Kaggle session
    llm_fn = openai_llm_fn()         # pa4.llm, points at http://localhost:8000/v1
    ...
    stop_server(proc)

The flags below work on a Kaggle T4 x2 with vLLM 0.33.0:
- Qwen3.5 is a vision-language model; --language-model-only skips the image encoder, which is what made
  start-up with CUDA graphs fit in memory (without it, only --enforce-eager worked).
- --max-num-seqs 32 is needed for the 9B: the default 256 exceeds its Mamba cache blocks.
- About 6 of the ~10 minutes of start-up is vLLM's own profiling/warm-up pass. No flag shortens it, so start
  the server ONCE per session and never restart it per experiment.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORT = 8000
MODELS = {
    "qwen3.5-9b": {"id": "Qwen/Qwen3.5-9B", "tp": 2},   # main model: both T4s
    "qwen3.5-4b": {"id": "Qwen/Qwen3.5-4B", "tp": 1},   # smaller model, for the optional capability comparison
}
FLAGS = ["--dtype", "half", "--max-model-len", "32768", "--gpu-memory-utilization", "0.90",
         "--language-model-only", "--max-num-batched-tokens", "4096", "--max-num-seqs", "32",
         "--enable-auto-tool-choice", "--tool-call-parser", "qwen3_coder", "--reasoning-parser", "qwen3"]


def server_command(name: str = "qwen3.5-9b", port: int = PORT) -> list[str]:
    m = MODELS[name]
    exe = shutil.which("vllm")
    head = [exe, "serve", m["id"]] if exe else [sys.executable, "-m", "vllm.entrypoints.cli.main", "serve", m["id"]]
    return head + ["--served-model-name", name, "--tensor-parallel-size", str(m["tp"]), "--port", str(port)] + FLAGS


def served_models(port: int = PORT) -> list[str] | None:
    """Names served on the port, or None if nothing answers."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/v1/models", timeout=5) as r:
            return [m["id"] for m in json.loads(r.read()).get("data", [])]
    except Exception:  # noqa: BLE001
        return None


def free_gpus() -> None:
    """Kill leftover vLLM processes. Cancelling a notebook cell does NOT stop a server it started."""
    subprocess.run(["pkill", "-9", "-f", "vllm serve|vllm.entrypoints|VLLM::"], capture_output=True)
    for _ in range(40):
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout.split()
        if not out or max(int(x) for x in out) < 1500:
            return
        time.sleep(3)


def start_server(name: str = "qwen3.5-9b", log_path="/kaggle/working/vllm.log", timeout_s: int = 1500,
                 port: int = PORT):
    """Start vLLM in the background and wait until it serves `name`. Returns the process.

    Healthy means the process is alive AND /v1/models lists our name (a leftover server from an earlier cell
    can answer /health). Raises RuntimeError with the log's last lines if it dies or times out.
    """
    if served_models(port) == [name]:
        print(f"{name} is already being served on port {port}; reusing it.")
        return None
    free_gpus()
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(server_command(name, port), stdout=open(log_path, "w"), stderr=subprocess.STDOUT,
                            start_new_session=True)
    t0, next_report = time.time(), 60
    while time.time() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"vLLM exited with code {proc.returncode}. Log tail:\n{_tail(log_path)}")
        if name in (served_models(port) or []):
            print(f"{name} is up after {time.time() - t0:.0f}s (log: {log_path})")
            return proc
        if time.time() - t0 > next_report:
            print(f"  loading... {time.time() - t0:.0f}s | {_tail(log_path, 1)[:150]}", flush=True)
            next_report += 60
        time.sleep(5)
    stop_server(proc)
    raise RuntimeError(f"vLLM did not come up in {timeout_s}s. Log tail:\n{_tail(log_path)}")


def stop_server(proc) -> None:
    if proc is not None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(proc.pid, sig)
                proc.wait(timeout=60)
                break
            except Exception:  # noqa: BLE001
                continue
    free_gpus()


def _tail(path, n: int = 25) -> str:
    try:
        lines = Path(path).read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(l for l in lines[-n:] if not re.search(r"shm_broadcast|No available shared memory", l))
