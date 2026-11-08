#!/usr/bin/env python3
"""Two-minute demo: see the full output without a model, a repo or real CVs.

Usage: python3 demo/run_demo.py [target_dir]     (default: ./hiring/demo)

Copies the db-owner fixture (brief, repo profile, approved rubric, 12 synthetic CVs in
md/pdf/docx), runs the real pipeline scripts (prepare -> redaction check -> validate -> rank ->
report) and uses scores recorded during the dry run in place of the model's scoring step.
Open <target>/report.html in a browser afterwards (report.md has the same content as text). Requires pdftotext for the PDF CVs.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "evals" / "fixtures" / "db-owner"
SCRIPTS = ROOT / "skills" / "screen-candidates" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_redaction  # noqa: E402
import identities  # noqa: E402
import prepare_cvs  # noqa: E402
import rank  # noqa: E402
import render_report  # noqa: E402

sys.path.insert(0, str(ROOT / "skills" / "interview-kit" / "scripts"))
import render_kit  # noqa: E402
import validate_kit  # noqa: E402


def step(n, text):
    print(f"\n[{n}/7] {text}")


def main(argv):
    target = Path(argv[1]) if len(argv) > 1 else Path.cwd() / "hiring" / "demo"
    if target.exists() and any(target.iterdir()):
        print(f"{target} already exists and is not empty. Pass another folder or delete it.")
        return 1
    target.mkdir(parents=True, exist_ok=True)

    step(1, "Copy brief, repo profile, approved rubric and 12 synthetic CVs")
    for name in ("brief.md", "repo-profile.md", "rubric.json", "jd.md"):
        shutil.copy(FIXTURE / name, target / name)
    shutil.copytree(FIXTURE / "cvs", target / "cvs")

    step(2, "Extract, redact and scan CVs for prompt injection (prepare_cvs.py)")
    if prepare_cvs.main(["prepare_cvs", str(target)]) != 0:
        return 1

    step(3, "Confirm names, then verify nothing identifying is left (identities.py + check_redaction.py)")
    # In real use the agent checks each detected name against the CV; the demo's names are synthetic.
    identities.main(["identities", "confirm", str(target), "--all"])
    if check_redaction.main(["check_redaction", str(target)]) != 0:
        return 1

    step(4, "Score candidates — in real use the model does this; the demo loads recorded scores")
    ids = {v: k for k, v in json.loads((target / "candidates.json").read_text()).items()}
    (target / "scores").mkdir()
    for fname, cid in ids.items():
        s = json.loads((FIXTURE / "reference-scores" / f"{fname}.json").read_text())
        s["candidate_id"] = cid
        (target / "scores" / f"{cid}.json").write_text(json.dumps(s, indent=2))
    print(f"  loaded {len(ids)} score files")

    step(5, "Validate scores and rank (validate_scores.py + rank.py)")
    if rank.main([str(target)]) != 0:
        return 1

    step(6, "Render the report (render_report.py)")
    notes = target / "notes.md"
    notes.write_text("- The job is defined by the brief's mission; the codebase is small, so criteria come from "
                     "the gaps it shows (migrations at app start, no test isolation, no backups).\n"
                     "- FastAPI expertise is deliberately not screened for: the team already has it.\n")
    render_report.main([str(target), "--notes", str(notes)])

    step(7, "Interview kits for three candidates — in real use the model writes them; the demo loads recorded ones")
    kits_src = FIXTURE / "interview-kits"
    kdir = target / "interviews"
    kdir.mkdir()
    shutil.copy(kits_src / "core.json", kdir / "core.json")
    for src in sorted(kits_src.glob("*.md.json")):
        fname = src.name[:-5]
        kit = json.loads(src.read_text())
        kit["candidate_id"] = ids[fname]
        (kdir / f"{ids[fname]}.json").write_text(json.dumps(kit, indent=2))
    if validate_kit.main([str(target)]) != 0:
        return 1
    render_kit.main([str(target)])

    print(f"\nDone. Open {target / 'report.html'} in your browser (text version: report.md)")
    print(f"Interview kits: {kdir / 'index.html'}")
    print("Next: install the plugin in Claude Code and ask it to plan a hire for your own repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
