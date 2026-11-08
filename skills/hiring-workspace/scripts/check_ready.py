#!/usr/bin/env python3
"""One gate for every skill: is the codebase understood, is the focus valid, what has been decided?

Usage: python3 check_ready.py <repo-or-workspace> [--role ROLE] [--stage STAGE] [--quiet]

Detects the mode:
  single-repo   <repo>/hiring/_repo/codebase-map.md must pass check_map.py (unchanged from earlier versions)
  workspace     a folder with workspace.json (or any folder inside it): every active repo needs a current map
                at its tier (full map for primary, service card for supporting) and system/system-map.md must
                pass check_system.py
With --role, also checks the role's focus (people-criteria and safeguard guard), lists artifacts written with an
older focus, and summarises decisions (confirmed and assumed) so the skill doesn't ask them again.
Prints the files the skill must read before it starts. Exit code 0 = ready, 1 = fix what it names first.
"""
import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "map-codebase" / "scripts"))
import check_map  # noqa: E402
import check_system  # noqa: E402
import decisions  # noqa: E402
import focus  # noqa: E402
import wslib  # noqa: E402


def run(fn, args):
    with redirect_stdout(io.StringIO()) as buf:
        rc = fn(args)
    return rc, buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--role")
    ap.add_argument("--stage", choices=decisions.STAGES)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    ctx = wslib.Context(a.target, a.role)
    ok = True
    lines = []

    if ctx.mode == "single":
        rc, out = run(check_map.main, [str(ctx.repo), "--quiet"])
        lines.append(f"Mode: single repo ({ctx.repo})")
        if rc:
            ok = False
            lines.append("FAIL codebase map: build or update it with the map-codebase skill")
            lines += ["  " + ln.strip() for ln in out.splitlines() if ln.strip().startswith(("error:", "FAIL"))][:12]
    else:
        rc, out = run(check_system.main, [str(ctx.ws), "--quiet"])
        lines.append(f"Mode: workspace {ctx.data.get('name')} ({ctx.ws}), {len(ctx.repo_names())} active repos")
        if rc:
            ok = False
            lines.append("FAIL workspace maps: map what is missing with map-codebase (full map for primary repos, "
                         "service card for supporting ones) and write system/system-map.md (hiring-workspace skill)")
            lines += ["  " + ln.strip() for ln in out.splitlines() if ln.strip().startswith("error:")][:15]

    reads = [str(m) for m in ctx.map_paths()]
    if ctx.mode == "workspace":
        reads.insert(0, str(ctx.ws / "system" / "system-map.md"))
    shared = decisions.load(ctx.shared_decisions)

    if a.role:
        rd = ctx.role_dir
        if not rd.exists():
            lines.append(f"Role folder {rd} does not exist yet (create it: "
                         + ("workspace.py new-role" if ctx.mode == "workspace" else "mkdir") + ")")
        text = focus.read_focus(rd)
        v = focus.version(text)
        errs, warns = focus.guard(text)
        if errs:
            ok = False
            lines.append(f"FAIL focus ({rd / 'focus.md'}):")
            lines += [f"  error: {e}" for e in errs]
        else:
            if text and rd.exists():
                focus.record(rd, text)
            lines.append(f"Focus: {v}" + (" (none set)" if not text else f" — {text[:140]!r}" + ("…" if len(text) > 140 else "")))
            lines += [f"  warn:  {w}" for w in warns]
            if text:
                reads.append(str(rd / "focus.md"))
            for name, why in focus.stale(rd, v):
                lines.append(f"  stale: {name}: {why}")
        role_dec = decisions.load(rd) if rd.exists() else []
        all_dec = shared + role_dec
        assumed = [x for x in all_dec if x["status"] == "assumed"]
        skipped = [x for x in all_dec if x["status"] == "skipped"]
        lines.append(f"Decisions: {len(all_dec) - len(assumed) - len(skipped)} answered, {len(skipped)} skipped (none)"
                     + (f", {len(assumed)} assumed" if assumed else "") + " "
                     f"(shared {ctx.shared_decisions}, role {decisions.path_for(rd)})")
        if a.stage:
            mine = [x for x in all_dec if x["stage"] == a.stage]
            if mine:
                lines.append(f"  already decided for {a.stage}: " + "; ".join(
                    f"{x['key']}={decisions.fmt(x['value'])[:40]}{' (skipped)' if x['status'] == 'skipped' else ' (assumed)' if x['status'] == 'assumed' else ''}"
                    for x in mine))
        for x in skipped[:8]:
            lines.append(f"  skipped: [{x['stage']}] {x['key']} = none — work without it (CHECKPOINTS.md, 'Skipped means none')")
        for x in assumed[:6]:
            lines.append(f"  assumed: [{x['stage']}] {x['key']} = {decisions.fmt(x['value'])[:60]} — confirm when the "
                         "hiring manager is back")
        lines.append(f"Role folder: {rd}")
    else:
        lines.append(f"Decisions (shared): {len(shared)}")
    lines.append("Read before starting: " + ", ".join(reads))
    lines.insert(0, "READY" if ok else "NOT READY")
    if not a.quiet or not ok:
        print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
