# PA4 report

Roll number:

At most 6 pages plus an appendix. Submit as `report.pdf` in the repository root. Replace every line in *italics*
with your own writing, and fill every table from your `summary.json` and `results.jsonl`. Add figures, rows or
columns where they help.

---

## R1. Interface ablation (A3)

*`solo` against `solo_naive_tools`: which tools help, by how much, and how attempts fail differently. `solo_mcp`
should match `solo` within noise; say whether it does.*

| Configuration | pass@1 [95% CI] | Tokens per attempt | Tokens per solved task |
|---|---|---|---|
| `solo` (your tools) | | | |
| `solo_naive_tools` | | | |
| `solo_mcp` (your tools over your MCP server) | | | |

Paired pass@1 difference [95% CI] (`solo_vs_solo_naive_tools` in `summary.json`):

*How failures differ between the two, with one transcript excerpt (quote it, and name the job id):*

---

## R2. Verification (A4)

*`solo` against `solo_noverify`: is the verification gate worth its cost?*

| Configuration | Solve rate [95% CI] | "Claimed done while tests fail" rate (`claimed_done_while_failing`) | Tokens per attempt |
|---|---|---|---|
| `solo` (gate on) | | | |
| `solo_noverify` (gate off) | | | |

Paired solve-rate difference [95% CI] (`solo_vs_solo_noverify` in `summary.json`):

*Your answer, with the numbers that support it:*

---

## R3. Team design (B1)

*What you changed in `TeamConfig`, the prompts or the context each worker receives, and why.*

| Change | Before | After | What you measured |
|---|---|---|---|
| | | | |

*What you observed:*

---

## R4. Is the team worth it? (B2)

| Configuration | pass@1 [95% CI] | pass@3 | pass^3 | Tokens per attempt | Tokens per solved task |
|---|---|---|---|---|---|
| `solo` | | | | | |
| `team` | | | | | |
| `solo_matched` | | | | | |

| Comparison | Wins / losses / ties | Paired pass@1 difference [95% CI] |
|---|---|---|
| `team` vs `solo` | | |
| `team` vs `solo_matched` | | |

*Your conclusion, in one paragraph, and how sure you are of it:*

---

## R5. Break it (B3)

| Configuration | Status (how runs ended) | Solve rate | Injection success rate | What the mitigation cost |
|---|---|---|---|---|
| `team_deceptive` | | | n/a | |
| `team_deceptive_trust` | | | n/a | |
| `team_inject_open` | | | | |
| `team_inject_gated` | | | | |
| `team_inject_lp` | | | | |

*What each mitigation bought and cost, and anything the model did that surprised you:*

---

## R6. Failure audit

*20 team transcripts, labelled in `artifacts/mast_audit.csv` with the MAST IDs (`artifacts/README.md` lists them).*

| MAST group | Failure modes seen (IDs) | Count |
|---|---|---|
| System design issues (FM-1.x) | | |
| Inter-agent misalignment (FM-2.x) | | |
| Task verification (FM-3.x) | | |

*Worked example 1: job id, the failure mode, and where in the transcript it first shows up (quote it):*

*Worked example 2:*

---

## R7. Noise and limits

*Run-to-run variation you observed (for example the same configuration on the same task across repeats or runs):*

*What would change your conclusions:*

*What you would run with more compute:*

---

## Appendix (optional)

*Extra tables, figures and longer transcript excerpts.*
