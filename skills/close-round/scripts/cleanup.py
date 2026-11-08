#!/usr/bin/env python3
"""Close a hiring round: delete candidate personal data, keep a pseudonymous audit record.

Usage:
  cleanup.py close <role_dir> [--keep-report] [--include-cvs] [--yes]
  cleanup.py sweep <hiring_dir> --older-than DAYS [--yes]

close   Without --yes, prints exactly what would be deleted and kept, then exits 3.
        With --yes, writes <role_dir>/audit.json and deletes. Never touches anything outside
        <role_dir>, and does not follow symlinks.
sweep   Lists rounds under <hiring_dir> that are still open and were opened more than DAYS ago.
        With --yes, closes each of them with default options.

Deleted:  extracted/ redacted/ scores/ runs/ prep_report.json candidates.json identities.json ranking.json
          notes.md report.md report.html eval-report.md golden.json interviews/
          (+ cvs/ with --include-cvs; report.md and report.html kept with --keep-report)
Kept:     brief.md jd.md repo-profile.md rubric.json rubric.md round.json audit.json
"""
import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

ALWAYS_DELETE = ["extracted", "redacted", "scores", "runs", "prep_report.json", "candidates.json", "identities.json",
                 "ranking.json", "notes.md", "report.md", "report.html", "eval-report.md", "golden.json", "interviews"]
KEEP = ["brief.md", "jd.md", "repo-profile.md", "rubric.json", "rubric.md", "round.json"]


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def size(p):
    if p.is_symlink() or p.is_file():
        return p.lstat().st_size
    return sum(f.lstat().st_size for f in p.rglob("*") if f.is_file() and not f.is_symlink())


def count_files(p):
    if p.is_symlink() or p.is_file():
        return 1
    return sum(1 for f in p.rglob("*") if f.is_file() or f.is_symlink())


def looks_like_role(role):
    return (role / "rubric.json").exists() and ((role / "candidates.json").exists() or (role / "round.json").exists())


def plan(role, keep_report, include_cvs):
    targets = [t for t in ALWAYS_DELETE if not (keep_report and t in ("report.md", "report.html"))]
    if include_cvs:
        targets.append("cvs")
    delete = [role / t for t in targets if (role / t).exists() or (role / t).is_symlink()]
    keep = [role / k for k in KEEP if (role / k).exists()]
    return delete, keep


def build_audit(role, keep_report, include_cvs):
    ranking_path = role / "ranking.json"
    rnd = load(role / "round.json") if (role / "round.json").exists() else {}
    audit = {
        "closed_at": now(),
        "opened_at": rnd.get("opened_at"),
        "rubric_version": None, "rubric_sha256": sha(role / "rubric.json"),
        "brief_sha256": sha(role / "brief.md") if (role / "brief.md").exists() else None,
        "candidates": None, "ranking_sha256": None, "results": [],
        "retained": {"report": keep_report, "cvs": not include_cvs},
        "note": ("Candidate ids are pseudonymous once candidates.json is deleted. "
                 + ("CVs were retained, so ids can be re-linked to people by re-running prepare_cvs.py."
                    if not include_cvs else "CVs were deleted; ids cannot be linked back to people from this record.")),
    }
    try:
        audit["rubric_version"] = load(role / "rubric.json").get("version")
    except Exception:  # noqa: BLE001
        pass
    if (role / "candidates.json").exists():
        audit["candidates"] = len(load(role / "candidates.json"))
    if ranking_path.exists():
        ranking = load(ranking_path)
        audit["ranking_sha256"] = sha(ranking_path)
        for r in ranking.get("ranked", []) + ranking.get("below_the_line", []):
            audit["results"].append({
                "candidate_id": r["candidate_id"], "rank": r.get("rank"), "tied": r.get("tied", False),
                "score": r["score"], "gate": r["gate"], "confidence": r.get("confidence"),
                # keep flag codes only; explanations can quote CV text
                "flags": sorted({str(f).split(":", 1)[0].strip() for f in r.get("flags", [])}),
            })
    return audit


def close(role, keep_report=False, include_cvs=False, yes=False, quiet=False):
    role = role.resolve()
    if not looks_like_role(role):
        print(f"ERROR: {role} does not look like a hiring round folder (needs rubric.json and candidates.json or round.json).")
        return 1
    rnd = load(role / "round.json") if (role / "round.json").exists() else {}
    if rnd.get("closed_at"):
        print(f"{role.name}: already closed at {rnd['closed_at']}.")
        return 0
    delete, keep = plan(role, keep_report, include_cvs)
    total = sum(size(p) for p in delete)
    n_files = sum(count_files(p) for p in delete)

    if not quiet or not yes:
        print(f"Round: {role}")
        print(f"Will delete {n_files} files ({total/1024:.0f} KB):")
        for p in delete:
            print(f"  - {p.relative_to(role)}{'/' if p.is_dir() and not p.is_symlink() else ''}")
        print("Will keep:")
        for p in keep:
            print(f"  + {p.relative_to(role)}")
        print("  + audit.json (new: pseudonymous scores, gates, hashes; no names or CV text)")
        if not include_cvs and (role / "cvs").exists():
            print("Note: cvs/ (the original CVs) is kept. Pass --include-cvs to delete them as well.")
        if keep_report and (role / "report.md").exists():
            print("Note: report.md and report.html are kept and contain candidate file names and quoted CV text.")
    if not yes:
        print("\nNothing deleted. Re-run with --yes to close the round.")
        return 3

    audit = build_audit(role, keep_report, include_cvs)
    audit["deleted"] = [str(p.relative_to(role)) for p in delete]
    audit["deleted_files"] = n_files
    (role / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    for p in delete:
        if p.is_symlink() or p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p)
    rnd["closed_at"] = audit["closed_at"]
    rnd.setdefault("opened_at", None)
    (role / "round.json").write_text(json.dumps(rnd, indent=2) + "\n", encoding="utf-8")
    print(f"Closed {role.name}: deleted {n_files} files; audit written to audit.json.")
    return 0


def sweep(hiring_dir, older_than, yes):
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=older_than)
    due = []
    for rf in sorted(Path(hiring_dir).glob("*/round.json")):
        rnd = load(rf)
        if rnd.get("closed_at") or not rnd.get("opened_at"):
            continue
        opened = dt.datetime.fromisoformat(rnd["opened_at"])
        if opened < cutoff:
            due.append((rf.parent, opened))
    if not due:
        print(f"No open rounds older than {older_than} days under {hiring_dir}.")
        return 0
    print(f"Open rounds older than {older_than} days:")
    for role, opened in due:
        print(f"  - {role.name} (opened {opened.date()}, {(dt.datetime.now(dt.timezone.utc) - opened).days} days ago)")
    if not yes:
        print("\nNothing deleted. Re-run with --yes to close all of them (CVs and reports are kept by default).")
        return 3
    rc = 0
    for role, _ in due:
        rc |= close(role, yes=True, quiet=True)
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("close")
    c.add_argument("role_dir")
    c.add_argument("--keep-report", action="store_true")
    c.add_argument("--include-cvs", action="store_true")
    c.add_argument("--yes", action="store_true")
    s = sub.add_parser("sweep")
    s.add_argument("hiring_dir")
    s.add_argument("--older-than", type=int, required=True)
    s.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "close":
        return close(Path(a.role_dir), a.keep_report, a.include_cvs, a.yes)
    return sweep(a.hiring_dir, a.older_than, a.yes)


if __name__ == "__main__":
    sys.exit(main())
