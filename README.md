# PA4: From Agent to Agent Team (starter repo)

CS5326 Advanced Generative AI and Agents. The full handout is `pa4_handout.pdf` in this folder; this file is the map.

## Running on Kaggle

`notebooks/pa4_kaggle.ipynb` runs your code against the real model:
1. Zip this folder (without `.venv/`, `runs/`, `pa4_out/` or `.git/`) and upload it as a private Kaggle dataset, attach it to the notebook (Add Input), and set
   `DATASET_DIR` in the "Get your code" cell to `/kaggle/input/datasets/<your-username>/<dataset-name>` (the Input
   panel shows the path). Or give a git URL.
2. Set GPU T4 x2 and Internet On.
3. In the notebook's configuration cell, set `EXPERIMENTS` to the experiments to run.
4. Click Kaggle's **Save Version** button (top right) and choose **Save & Run All (Commit)**.

The notebook installs the stack, checks your code with the smoke tests, starts vLLM (`pa4/serve.py`, ~10 min),
runs the configurations defined in `pa4/experiments.py`, and summarises them with your `eval.py`. Results are written
one row per attempt as they finish, and a re-run skips finished attempts.

## Setup

Python 3.10 to 3.12 (3.11 recommended).

```bash
pip install -r requirements.txt
python -m pytest tests -q        # public smoke tests: each fails until you implement the part it tests
```

Everything in `tests/` runs offline with a scripted fake model (`pa4.llm.ScriptedLLM`); no GPU needed. The real
model (Qwen3.5-9B served by vLLM) runs on Kaggle; see the handout.

## What is yours

| File | Part | Yours? |
|---|---|---|
| `pa4/agent.py` | A1 the loop, A4 verify-before-done | **Yes**: `parse_tool_calls`, `run_agent` |
| `pa4/mcp_server.py` | A2 tools over MCP | **Yes**: `build_mcp_server`, `mcp_tools_to_openai`, `call_result_to_text` |
| `pa4/tools.py` | A3 agent-computer interface | **Yes**: `view_file`, `search_code`, `edit_file`, `edit_lines`, their specs in `TOOL_SPECS` |
| `pa4/context.py` | A3 context engineering | **Yes**: `truncate_output`, `compact_history` |
| `pa4/team.py` | B1 the LangGraph team, B3 mitigations | **Yes**: the five nodes, `build_team_graph`, `run_team`, `needs_approval`, `GatedToolBox.call`, `coder_tools`, `tester_tools` |
| `pa4/eval.py` | B2 is the team worth it? | **Yes**: `pass_at_k`, `pass_hat_k`, `matched_budget_solo`. The suite score, bootstrap CIs, head-to-head counts and `run_grid` are provided |
| `pa4/faults.py` | B3 deceptive tester, prompt injection, shell honeypot, approvers | Provided: do not edit |
| `pa4/experiments.py` | the experiment configurations, `make_jobs`, `summarize`, `compare` | Provided |
| `pa4/serve.py` | starts vLLM on Kaggle with the confirmed flags | Provided |
| `pa4/tasks.py` | task sandbox, hidden test runner | Provided: do not edit |
| `pa4/llm.py` | model access (`openai_llm_fn`, `ScriptedLLM`, `RoutedLLM` for teams) | Provided |
| `pa4/mcp_bridge.py` | lets the agent use an MCP session | Provided |
| `pa4/trace.py` | JSONL traces | Provided |
| `submission_adapter.py` | the only entry points the graders call | Keep the signatures |

Every function you write has a docstring with its exact contract. The hidden tests check those contracts.

## Tasks

`tasks/dev/` holds the 10 development tasks: small buggy repositories, each with an `ISSUE.md` and a `tests/`
folder that the agent cannot read. Some have a spec in `docs/`.

| Task | Kind of difficulty |
|---|---|
| `roman`, `deep_merge`, `ratelimit` | Well-specified fixes |
| `retry`, `pages` | Several bugs across two files |
| `split`, `ttlcache` | A precise contract with edge cases (largest-remainder rounding, expiry and recency) |
| `table`, `units`, `resolver` | Unicode width, a long file with scattered bugs, a hidden scale requirement |

## Section B in one picture

```
supervisor --handoff(coder)--> coder ----------------------------+--> supervisor
           --handoff(tester)-> tester (read-only tools) ---------+
           --handoff(finish)-> gate --tests pass--> END
                                    --tests fail--> supervisor   (unless you trust the claim)
coder --risky call queued--> approval --interrupt() / approver--> supervisor
```

The Coder and Tester are your Section A agent with their own prompts and tool sets. Every node returns a
LangGraph `Command`; a checkpointer makes a crashed run resumable by thread id. All model calls still go through
an LLMFn, so `RoutedLLM` can script each role offline.

## Rules

- **Section A: no agent frameworks.** Plain Python, the `openai` client (already wrapped in `pa4/llm.py`) and the
  `mcp` SDK. No LangChain, LangGraph, LlamaIndex, smolagents, etc. in `pa4/agent.py`, `tools.py`, `context.py`
  or `mcp_server.py`.
- **Section B: LangGraph is the only framework**, for the graph, checkpointing and interrupts in `pa4/team.py`.
- Never read or copy a task's `tests/` into the agent's context; the tools already refuse to.
- Keep your copy of this repository private. Do not fork it publicly: a public fork shows your solution to everyone.
- The Section B tests run your Section A agent as the Coder and the Tester, so finish A1 and the A3 tool specs first.

## Submitting

Write your report (`report_template.md` has the sections and tables to start from) and export it as `report.pdf`. Put your Kaggle `results.jsonl` and `summary.json`, your `mast_audit.csv` and `report.pdf` in place (see `artifacts/README.md`), then run `python make_submission.py <roll_number>` and upload the zip to LMS.
