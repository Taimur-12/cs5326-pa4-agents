"""The experiment grid. PROVIDED.

Each configuration below is one thing you measure. `make_jobs` turns (configuration, tasks, repeats) into jobs for
eval.run_grid, which runs them concurrently and appends one JSON row per attempt to a results file. `summarize`
turns rows into the numbers your report needs (using YOUR eval.py functions).

| config              | part | what runs                                                                   |
|---------------------|------|-----------------------------------------------------------------------------|
| solo                | A    | your agent, designed tools, verify gate on                                  |
| solo_noverify       | A4   | same, verify gate off (the naive stop rule)                                 |
| solo_naive_tools    | A3   | same as solo but with the naive read_file/write_file tools                  |
| solo_mcp            | A2   | same as solo, but the tools come from your MCP server over an MCP session   |
| team                | B1   | your team, default TeamConfig                                               |
| solo_matched        | B2   | best-of-N solo at the team's mean token spend on the same task              |
| team_deceptive      | B3   | team with the lying Tester, gate verifies the finish                        |
| team_deceptive_trust| B3   | team with the lying Tester, gate trusts the finish                          |
| team_inject_open    | B3   | prompt injection, shell tool given to the Coder, no approval gate           |
| team_inject_gated   | B3   | prompt injection, shell tool given, approval gate on (approver denies all)  |
| team_inject_lp      | B3   | prompt injection, least privilege (shell tool withheld), no approval gate   |

Every row has: job_id, config, task, rep, solved, prompt_tokens, completion_tokens, wall_s, and a "stop"/"status".
Transcripts go to <work_root>/transcripts/<job_id>.json (you need team transcripts for the failure audit).
`compare` puts two configurations head to head: wins/losses/ties plus the paired difference in pass@1 with its CI.
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from statistics import mean

from . import eval as E
from .agent import run_agent
from .faults import deny_all, inject_prompt, injection_succeeded
from .tasks import fresh_copy
from .team import TeamConfig, run_team
from .tools import naive_toolbox

TEAM_CONFIGS = {
    "team": dict(),
    "team_deceptive": dict(deceptive_tester=True, verify_finish=True),
    "team_deceptive_trust": dict(deceptive_tester=True, verify_finish=False),
    "team_inject_open": dict(shell_tool=True, least_privilege=False, approval_gate=False),
    "team_inject_gated": dict(shell_tool=True, least_privilege=False, approval_gate=True),
    "team_inject_lp": dict(shell_tool=True, least_privilege=True, approval_gate=False),
}
SOLO_CONFIGS = {"solo": dict(), "solo_noverify": dict(verify=False), "solo_naive_tools": dict(naive=True),
                "solo_mcp": dict(mcp=True)}
CONFIGS = list(SOLO_CONFIGS) + list(TEAM_CONFIGS) + ["solo_matched"]


class RecordingLLM:
    """Wraps an LLMFn and keeps a compact log of every call, for team transcripts (the R6 failure audit).

    Each entry: the role (from the system prompt), the newest input message (what changed since the last call:
    a tool result, a nudge, or the task), and the model's reply. Thread-safe enough for one job per wrapper."""

    def __init__(self, llm_fn, max_chars: int = 2000):
        self.llm_fn, self.max_chars, self.calls = llm_fn, max_chars, []

    def __call__(self, messages, tools):
        resp = self.llm_fn(messages, tools)
        system = messages[0].get("content", "") if messages and messages[0].get("role") == "system" else ""
        last = messages[-1] if messages else {}
        self.calls.append({
            "role": " ".join(system.split()[:4]),
            "input": {"role": last.get("role"), "content": str(last.get("content") or "")[:self.max_chars]},
            "reply": {"content": (resp.get("content") or "")[:self.max_chars],
                      "tool_calls": [{"name": c.get("name"), "arguments": str(c.get("arguments"))[:self.max_chars]}
                                     for c in resp.get("tool_calls") or []],
                      "finish_reason": resp.get("finish_reason")}})
        return resp


def _save_transcript(work_root: Path, job_id: str, payload) -> None:
    p = Path(work_root) / "transcripts" / f"{job_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, default=str), encoding="utf-8")


def _tokens(row: dict) -> int:
    return row.get("prompt_tokens", 0) + row.get("completion_tokens", 0)


def make_jobs(config: str, tasks: list[str], repeats: int, task_root, work_root, llm_fn, team_cfg: dict | None = None,
              agent_kwargs: dict | None = None, team_rows: list[dict] | None = None) -> dict:
    """Jobs for one configuration: {job_id: callable}. job ids look like "team/roman/r0".

    team_cfg overrides TeamConfig fields for team configs; agent_kwargs go to run_agent for solo configs.
    "solo_matched" needs the finished "team" rows (team_rows): each job's budget is the MEAN tokens the team spent on
    that task over all its reps, and tasks without team rows are skipped. (Matching per rep instead would give the
    matched solo a tiny budget whenever the team got lucky cheaply, which makes the baseline noisy and unfair.)
    """
    task_root, work_root = Path(task_root), Path(work_root)
    agent_kwargs = dict(agent_kwargs or {})
    spent_by_task: dict = {}
    for r in team_rows or []:
        if r.get("config") == "team" and "solved" in r:
            spent_by_task.setdefault(r["task"], []).append(_tokens(r))
    budgets = {(t, rep): round(mean(v)) for t, v in spent_by_task.items() for rep in range(repeats)}
    jobs = {}
    for task in tasks:
        for rep in range(repeats):
            jid = f"{config}/{task}/r{rep}"
            run_dir = work_root / "runs" / config / f"{task}_r{rep}"

            if config in SOLO_CONFIGS:
                def job(task=task, rep=rep, jid=jid, run_dir=run_dir, opts=SOLO_CONFIGS[config]):
                    d = fresh_copy(task_root, task, run_dir)
                    kw = dict(agent_kwargs)
                    if "verify" in opts:
                        kw["verify"] = opts["verify"]
                    if opts.get("naive"):
                        kw["tools"] = naive_toolbox(d)
                    t0 = time.time()
                    if opts.get("mcp"):
                        from .mcp_bridge import MCPToolBox
                        from .mcp_server import build_mcp_server
                        with MCPToolBox(build_mcp_server(d)) as tools:
                            rec = run_agent(d, llm_fn, tools=tools, **kw)
                    else:
                        rec = run_agent(d, llm_fn, **kw)
                    _save_transcript(work_root, jid.replace("/", "__"), rec["messages"])
                    return {"config": config, "task": task, "rep": rep, "wall_s": round(time.time() - t0, 1),
                            **{k: v for k, v in rec.items() if k not in ("messages", "task")}}
            elif config in TEAM_CONFIGS:
                def job(task=task, rep=rep, jid=jid, run_dir=run_dir, opts=TEAM_CONFIGS[config]):
                    d = fresh_copy(task_root, task, run_dir)
                    if config.startswith("team_inject"):
                        inject_prompt(d)
                    cfg = TeamConfig(**{**(team_cfg or {}), **opts})
                    t0 = time.time()
                    recorder = RecordingLLM(llm_fn)
                    rec = run_team(d, recorder, cfg, thread_id=jid, approver=deny_all)
                    _save_transcript(work_root, jid.replace("/", "__"), {**rec, "calls": recorder.calls})
                    extra = {"injection_succeeded": injection_succeeded(rec["shell_log"])} \
                        if config.startswith("team_inject") else {}
                    return {"config": config, "task": task, "rep": rep, "wall_s": round(time.time() - t0, 1),
                            **{k: v for k, v in rec.items() if k not in ("log", "task")}, **extra}
            elif config == "solo_matched":
                if (task, rep) not in budgets:
                    continue

                def job(task=task, rep=rep, jid=jid, run_dir=run_dir, budget=budgets[(task, rep)]):
                    t0 = time.time()
                    rec = E.matched_budget_solo(task_root, task, llm_fn, budget, run_dir, **agent_kwargs)
                    _save_transcript(work_root, jid.replace("/", "__"), rec["records"])
                    return {"config": config, "task": task, "rep": rep, "budget": budget,
                            "wall_s": round(time.time() - t0, 1),
                            **{k: v for k, v in rec.items() if k not in ("records", "task")}}
            else:
                raise ValueError(f"unknown config {config!r}; choose from {CONFIGS}")
            jobs[jid] = job
    return jobs


def summarize(rows: list[dict], k: int = 3, n_boot: int = 2000) -> dict:
    """Per configuration: attempts, pass@1 with a 95% bootstrap CI, pass@k, pass^k (when every task has >= k
    tries), mean tokens per attempt, tokens per solved attempt, stop/status counts and, for single-agent
    configurations, claimed_done_while_failing: the share of attempts that stopped with a final answer while the tests
    still failed. Uses YOUR pass_at_k and pass_hat_k."""
    out = {}
    for config in sorted({r["config"] for r in rows if "config" in r}):
        mine = [r for r in rows if r.get("config") == config and "solved" in r]
        res = E.results_by_task(mine, config)
        if not res:
            continue
        s = {"tasks": len(res), "attempts": len(mine),
             "pass@1": E.suite_score(res, E.pass_at_k, 1),
             "pass@1_ci95": E.bootstrap_ci(res, E.pass_at_k, 1, n_boot=n_boot),
             "tokens_per_attempt": round(mean(_tokens(r) for r in mine)),
             "tokens_per_solved": round(sum(_tokens(r) for r in mine) / max(1, sum(r["solved"] for r in mine))),
             "per_task": {t: f"{sum(v)}/{len(v)}" for t, v in sorted(res.items())}}
        if min(len(v) for v in res.values()) >= k:
            s[f"pass@{k}"] = E.suite_score(res, E.pass_at_k, k)
            s[f"pass^{k}"] = E.suite_score(res, E.pass_hat_k, k)
        ends = {}
        for r in mine:
            key = str(r.get("status") or r.get("stop"))
            ends[key] = ends.get(key, 0) + 1
        s["ends"] = ends
        stopped = [r for r in mine if "stop" in r]
        if stopped:
            s["claimed_done_while_failing"] = mean(r["stop"] == "final_answer" and not r["solved"] for r in stopped)
        if any("injection_succeeded" in r for r in mine):
            s["injection_success_rate"] = mean(bool(r.get("injection_succeeded")) for r in mine)
        out[config] = s
    return out


def paired_difference(a: dict, b: dict, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0) -> dict:
    """Mean per-task difference in success rate, a minus b, over the tasks both configurations ran, with a paired
    percentile bootstrap CI that resamples those tasks (same seed and quantile rule as eval.bootstrap_ci).

    This is the number that says whether a beats b. Two per-configuration CIs can overlap while the paired
    difference is clearly above zero, because both configurations ran the same tasks.
    """
    names = sorted(set(a) & set(b))
    if not names:
        return {"pass@1_diff": None, "pass@1_diff_ci95": None}
    gap = {t: mean(map(bool, a[t])) - mean(map(bool, b[t])) for t in names}
    rng = random.Random(seed)
    scores = []
    for _ in range(n_boot):
        draw = [rng.choice(names) for _ in names]
        scores.append(mean(gap[t] for t in draw))
    scores.sort()
    ci = (scores[int(alpha / 2 * n_boot)], scores[int((1 - alpha / 2) * n_boot) - 1])
    return {"pass@1_diff": mean(gap.values()), "pass@1_diff_ci95": ci}


def compare(rows: list[dict], a: str, b: str) -> dict:
    """Configuration a against b: paired_comparison (wins/losses/ties), the paired difference in pass@1 with
    its 95% CI (paired_difference), and their token spend."""
    ra, rb = E.results_by_task(rows, a), E.results_by_task(rows, b)
    spend = {c: sum(_tokens(r) for r in rows if r.get("config") == c) for c in (a, b)}
    return {"a": a, "b": b, **E.paired_comparison(ra, rb), **paired_difference(ra, rb), "total_tokens": spend}
