# artifacts/

Put your submission artifacts here (see the handout, section "Submission"):

- `results.jsonl`, `summary.json`, `transcripts/`: unzip `pa4_outputs.zip` (from your Kaggle run) into this folder.
  After a `CONTINUE_FROM` commit, unzip the earlier version's zip first, then the newer one. Include every row.
- `mast_audit.csv`: your hand-labelled audit of 20 team transcripts (handout R6). One row per transcript:
  - `job_id`: e.g. `team/table/r1`
  - `solved`: `true` / `false`
  - `mast_failure_modes`: the IDs of the MAST failure mode(s) you observed, separated by `;` (e.g. `FM-2.4;FM-3.2`),
    or `none`. Use the IDs below.
  - `first_step`: where the first failure shows up, e.g. `call 14 (Coder)`
  - `justification`: one line, quoting or pointing at the transcript

`make_submission.py` adds the transcripts named in `mast_audit.csv` (and only those) to your zip.

## MAST failure modes (Cemri et al., arXiv 2503.13657)

| Group | ID | Failure mode |
|---|---|---|
| System design issues | FM-1.1 | Disobey task specification |
| | FM-1.2 | Disobey role specification |
| | FM-1.3 | Step repetition |
| | FM-1.4 | Loss of conversation history |
| | FM-1.5 | Unaware of stopping conditions |
| Inter-agent misalignment | FM-2.1 | Conversation reset |
| | FM-2.2 | Fail to ask for clarification |
| | FM-2.3 | Task derailment |
| | FM-2.4 | Information withholding |
| | FM-2.5 | Ignored other agent's input |
| | FM-2.6 | Reasoning-action mismatch |
| Task verification | FM-3.1 | Premature termination |
| | FM-3.2 | No or incomplete verification |
| | FM-3.3 | Incorrect verification |

Read the paper's definitions before labelling; the handout's R6 section says what to submit.
