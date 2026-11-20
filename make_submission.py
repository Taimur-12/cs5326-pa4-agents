"""Build <roll_number>_pa4.zip for LMS. Works on Windows, macOS and Linux.

Usage:  python make_submission.py <roll_number>
"""
import csv
import subprocess
import sys
import zipfile
from pathlib import Path

REQUIRED = ["submission_adapter.py", "pa4/agent.py", "pa4/team.py", "pa4/eval.py", "artifacts/results.jsonl",
            "artifacts/summary.json", "artifacts/mast_audit.csv", "report.pdf"]
TOP_LEVEL = ["submission_adapter.py", "artifacts/results.jsonl", "artifacts/summary.json", "artifacts/mast_audit.csv",
             "report.pdf"]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python make_submission.py <roll_number>")
        return 1
    roll = sys.argv[1]
    root = Path(__file__).resolve().parent
    missing = [f for f in REQUIRED if not (root / f).is_file()]
    for f in missing:
        print(f"MISSING: {f}")
    if missing:
        print("Fix the missing files above, then re-run.")
        return 1

    smoke = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"], cwd=root,
                           capture_output=True, text=True)
    if smoke.returncode == 0:
        print("smoke tests: pass")
    else:
        print("WARNING: some smoke tests fail (python -m pytest tests -q). Submitting anyway.")

    with open(root / "artifacts" / "mast_audit.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 20:
        print(f"WARNING: mast_audit.csv has {len(rows)} rows; the audit asks for 20.")
    audited = []
    for row in rows:
        job_id = (row.get("job_id") or "").strip()
        if not job_id:
            continue
        name = f"artifacts/transcripts/{job_id.replace('/', '__')}.json"
        if (root / name).is_file():
            audited.append(name)
        else:
            print(f"WARNING: no transcript for {job_id} (expected {name}). Unzip pa4_outputs.zip into artifacts/.")

    out = root / f"{roll}_pa4.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted((root / "pa4").rglob("*.py")):
            z.write(p, p.relative_to(root).as_posix())
        for f in TOP_LEVEL + sorted(set(audited)):
            z.write(root / f, f)
    print(f"added {len(set(audited))} audited transcripts")
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB). Upload it to LMS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
