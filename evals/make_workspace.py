#!/usr/bin/env python3
"""Create an eval workspace from a fixture: copies brief, profile, rubric and CVs, generates
counterfactual CV variants from golden.json, and runs prepare_cvs.py + check_redaction.py.

Usage: python3 evals/make_workspace.py evals/fixtures/db-owner <repo>/hiring/eval-db-owner

Then screen the candidates N times, each in a FRESH agent session, writing scores to
<workspace>/runs/run-<k>/scores (see evals/README.md), and run evals/evaluate.py.
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "screen-candidates" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import hiring_lib as H  # noqa: E402


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    fixture, ws = Path(argv[1]), Path(argv[2])
    if ws.exists() and any(ws.iterdir()):
        print(f"ERROR: {ws} exists and is not empty", file=sys.stderr)
        return 1
    ws.mkdir(parents=True, exist_ok=True)
    for name in ("brief.md", "repo-profile.md", "rubric.json", "rubric.md", "jd.md"):
        if (fixture / name).exists():
            shutil.copy(fixture / name, ws / name)
    shutil.copytree(fixture / "cvs", ws / "cvs")

    golden = H.load_json(fixture / "golden.json")
    shutil.copy(fixture / "golden.json", ws / "golden.json")
    for group in golden.get("counterfactuals", []):
        base = (fixture / "cvs" / group["base"]).read_text(encoding="utf-8")
        for v in group["variants"]:
            text = base
            for old, new in v["replace"].items():
                if old not in text:
                    print(f"ERROR: {v['file']}: {old!r} not found in {group['base']}", file=sys.stderr)
                    return 1
                text = text.replace(old, new)
            (ws / "cvs" / v["file"]).write_text(text, encoding="utf-8")

    py = sys.executable
    rc = subprocess.call([py, "-I", str(SCRIPTS / "prepare_cvs.py"), str(ws)])
    # Fixture names are synthetic and verified by the fixture author; real rounds confirm each one.
    rc |= subprocess.call([py, "-I", str(SCRIPTS / "identities.py"), "confirm", str(ws), "--all"])
    rc |= subprocess.call([py, "-I", str(SCRIPTS / "check_redaction.py"), str(ws)])
    print(f"\nWorkspace ready: {ws}" if rc == 0 else "\nWorkspace created, but preparation reported problems.")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
