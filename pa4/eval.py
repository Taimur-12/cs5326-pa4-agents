"""Is the team worth it? (B2). pass@k, pass^k and the matched-budget baseline are YOURS; the suite score, bootstrap
CIs, head-to-head counts and the grid runner are PROVIDED.

The comparison that matters: solo agent vs team **at a matched token budget**. A team spends more tokens per
task than one agent, so "the team solved more" means nothing until the solo agent gets the same spend
(here: repeated independent attempts, best-of-N, until it has used as many tokens as the team did).

Reliability: pass@k answers "does at least one of k tries work?"; pass^k (tau-bench) answers "do ALL k tries
work?", which is what you need before trusting an agent unattended. Report both, per configuration, with
bootstrap confidence intervals that resample TASKS (tries on the same task are not independent).
"""
from __future__ import annotations

import json
import random
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import comb
from pathlib import Path
from statistics import mean

from .agent import run_agent
from .tasks import fresh_copy


# ---------------------------------------------------------------------------------------------------------
# YOURS: reliability metrics for one task.
# ---------------------------------------------------------------------------------------------------------
def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k for one task with c successes in n tries: 1 - C(n-c, k) / C(n, k).
    1.0 when n - c < k. Raise ValueError unless 0 <= c <= n and 1 <= k <= n."""
    raise NotImplementedError("TODO B2: pass_at_k")


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k for one task: the probability that k tries drawn without replacement from the n all succeed,
    C(c, k) / C(n, k). Same ValueError rules as pass_at_k."""
    raise NotImplementedError("TODO B2: pass_hat_k")


# ---------------------------------------------------------------------------------------------------------
# PROVIDED: suite scores, bootstrap CIs and head-to-head counts. `results` maps task name -> list of
# booleans (one per independent try). Read them: your report interprets their output.
# ---------------------------------------------------------------------------------------------------------
def suite_score(results: dict, metric, k: int) -> float:
    """Mean over tasks of metric(n, c, k), where n and c are the task's tries and successes."""
    return mean(metric(len(v), sum(map(bool, v)), k) for v in results.values())


def bootstrap_ci(results: dict, metric, k: int, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0):
    """Percentile bootstrap CI for suite_score(results, metric, k), resampling TASKS with replacement.

    Use random.Random(seed); draw n_boot resamples, each len(results) task names chosen with rng.choice from the
    sorted task names; score each resample like suite_score (a task drawn twice counts twice). Return
    (lo, hi) = the alpha/2 and 1 - alpha/2 quantiles of the sorted scores, taking element
    int(alpha/2 * n_boot) and element int((1 - alpha/2) * n_boot) - 1.
    """
    rng = random.Random(seed)
    names = sorted(results)
    scores = []
    for _ in range(n_boot):
        draw = [rng.choice(names) for _ in names]
        scores.append(mean(metric(len(results[t]), sum(map(bool, results[t])), k) for t in draw))
    scores.sort()
    return scores[int(alpha / 2 * n_boot)], scores[int((1 - alpha / 2) * n_boot) - 1]


def paired_comparison(a: dict, b: dict) -> dict:
    """Per-task head-to-head on the tasks both configurations ran. A task is a win for a if a's success rate
    (successes / tries) is higher, a loss if lower, a tie if equal. Return {"wins": [...], "losses": [...],
    "ties": [...]}, each a sorted list of task names."""
    out = {"wins": [], "losses": [], "ties": []}
    for t in sorted(set(a) & set(b)):
        ra, rb = mean(map(bool, a[t])), mean(map(bool, b[t]))
        out["wins" if ra > rb else "losses" if ra < rb else "ties"].append(t)
    return out


# ---------------------------------------------------------------------------------------------------------
# YOURS: the matched-budget baseline
# ---------------------------------------------------------------------------------------------------------
def matched_budget_solo(task_root, task: str, llm_fn, token_budget: int, work_dir, max_attempts: int = 20,
                        **agent_kwargs) -> dict:
    """Best-of-N solo baseline at a token budget.

    Run independent solo attempts, each on a fresh copy (fresh_copy(task_root, task, work_dir / f"attempt_{i}")),
    one after another, until one is solved, the budget is spent, or max_attempts is reached. Each attempt gets
    max_tokens = the budget left (pass it to run_agent along with agent_kwargs). Stop before an attempt when no
    budget is left. Return {"task", "solved" (any attempt solved), "attempts", "prompt_tokens",
    "completion_tokens" (totals over attempts), "records" (the run_agent records without their "messages")}.
    """
    raise NotImplementedError("TODO B2: matched_budget_solo")


# ---------------------------------------------------------------------------------------------------------
# PROVIDED: run a grid of jobs concurrently, resumably
# ---------------------------------------------------------------------------------------------------------
def run_grid(jobs: dict, out_path, concurrency: int = 12, on_result=None) -> list[dict]:
    """Run jobs concurrently and append each result to a JSONL file as soon as it finishes.

    jobs: {job_id: zero-argument callable returning a JSON-serialisable dict}. Jobs that already have a finished
    row (one with "solved") in out_path are skipped, so re-running after a Kaggle timeout continues where it
    stopped. A job that raises is recorded as {"job_id", "error", "trace"} and runs again the next time, so a
    crash you have fixed does not leave a hole. Returns all rows in the file (old and new).

    Use concurrency around 12 with the 9B on two T4s: with many more attempts at once the server can stall.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if "solved" in row:
                done.add(row["job_id"])
    todo = {jid: fn for jid, fn in jobs.items() if jid not in done}
    lock = threading.Lock()

    def one(jid, fn):
        try:
            row = {"job_id": jid, **fn()}
        except Exception as e:  # noqa: BLE001
            row = {"job_id": jid, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}
        with lock, out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        if on_result:
            on_result(row)
        return row

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for fut in as_completed([ex.submit(one, jid, fn) for jid, fn in todo.items()]):
            fut.result()
    return [json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()]


def results_by_task(rows: list[dict], config: str) -> dict:
    """PROVIDED. {task: [solved, ...]} for the rows of one configuration (rows need "config", "task", "solved")."""
    out: dict = {}
    for r in rows:
        if r.get("config") == config and "solved" in r:
            out.setdefault(r["task"], []).append(bool(r["solved"]))
    return out
