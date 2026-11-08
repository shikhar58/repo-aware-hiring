#!/usr/bin/env python3
"""Gate for a multi-repo workspace: is every repo mapped at its tier, and does system-map.md explain how they connect?

Usage: python3 check_system.py <workspace> [--quiet] [--skip-maps]

Checks:
  - every active repo has a current map: a full codebase map (primary) or a service card (supporting)
    (skipped with --skip-maps)
  - system/system-map.md exists, has the required sections, and carries the current graph hash
    (the graph is rebuilt from fresh inventories, so code changes in any repo make it stale)
  - every repo is named in Repositories; every link in the graph is explained in Connections (or, for shared
    contracts, in Shared code and templates); every template group is named; Ownership says something
    ("unknown" is allowed)
  - no secret-looking values were copied in
Exit code 0 = ready, 1 = fix the maps or the system map first.
"""
import argparse
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "map-codebase" / "scripts"))
import check_map  # noqa: E402
import system_graph  # noqa: E402
import wslib  # noqa: E402

SECTIONS = {
    "overview": r"overview",
    "repos": r"repositor|repos\b",
    "connections": r"connections|how .* connect|dependencies between",
    "shared": r"shared|templates?",
    "ownership": r"owner|teams?",
    "gaps": r"gaps|unknowns|not covered",
}
TITLES = {"overview": "Overview", "repos": "Repositories", "connections": "Connections",
          "shared": "Shared code and templates", "ownership": "Ownership and team boundaries",
          "gaps": "Gaps"}


def parse(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = next((k for k, p in SECTIONS.items() if k not in out and re.search(p, m.group(1), re.I)), None)
            if cur:
                out[cur] = []
            continue
        if cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def named(text, name):
    return re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text, re.I) is not None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ws")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--skip-maps", action="store_true")
    a = ap.parse_args(argv)
    ws = wslib.find_workspace(a.ws)
    errors, warnings = [], []
    if not ws:
        print(f"FAIL: no workspace at {a.ws}")
        return 1
    data = wslib.load(ws)
    active = wslib.active_repos(data)
    if not active:
        errors.append("the workspace has no repos (add them with workspace.py add)")
    if active and not any(r.get("tier") == "primary" for r in active):
        errors.append("no repo is marked primary: mark the repos the hire will mainly work in (workspace.py tier)")

    if not a.skip_maps:
        for r in active:
            path, mp = wslib.repo_path(ws, r), wslib.map_file(ws, r)
            level = "full" if r.get("tier") == "primary" else "card"
            if not path.is_dir():
                errors.append(f"{r['name']}: checkout missing at {path}")
                continue
            with redirect_stdout(io.StringIO()) as buf:
                rc = check_map.main([str(path), "--map", str(mp), "--level", level, "--quiet"])
            if rc:
                errs = [ln.strip()[7:] for ln in buf.getvalue().splitlines() if ln.strip().startswith("error:")] or \
                    ["missing" if not mp.exists() else buf.getvalue().strip()[:200]]
                errors.append(f"{r['name']}: {'codebase map' if level == 'full' else 'service card'} not ready "
                              f"({mp.relative_to(ws)}): " + "; ".join(errs[:3]) + (" …" if len(errs) > 3 else ""))

    invs, missing = system_graph.load_inventories(ws, data, fresh=True)
    g = system_graph.build(data, invs)
    sm = ws / "system" / "system-map.md"
    if len(active) > 1:
        if not sm.exists():
            errors.append(f"no system map at {sm.relative_to(ws)} (run system_graph.py, then write it with the "
                          "hiring-workspace skill)")
        else:
            text = sm.read_text(encoding="utf-8")
            m = re.search(r"Graph:\s*`?([0-9a-f]{8,64})", text)
            if not m:
                errors.append("system map has no 'Graph: <hash>' header (copy it from system/system-graph.md)")
            elif not g["hash"].startswith(m.group(1)):
                errors.append(f"STALE: repos, tiers or links changed since the system map was written (graph is now "
                              f"{g['hash']}); run system_graph.py and update Connections")
            secs = parse(text)
            for k, t in TITLES.items():
                if k not in secs:
                    errors.append(f"system map: missing section ## {t}")
                elif len(secs[k]) < 15:
                    errors.append(f"system map: section '{t}' is empty")
            for r in active:
                if not named(secs.get("repos", ""), r["name"]):
                    errors.append(f"system map: repo '{r['name']}' is not described in Repositories")
            for e in g["edges"]:
                where = secs.get("shared", "") + "\n" + secs.get("connections", "") if e["kind"] == "contract" \
                    else secs.get("connections", "")
                lines = [ln for ln in where.splitlines() if named(ln, e["from"]) and named(ln, e["to"])]
                if not lines:
                    errors.append(f"system map: link {e['from']} -[{e['kind']}]-> {e['to']} ({e['detail']}) is not "
                                  "explained in Connections (one line naming both repos)")
            for t in g["templates"]:
                missing_names = [n for n in t["repos"] if not named(secs.get("shared", ""), n)]
                if missing_names:
                    errors.append(f"system map: repos {', '.join(t['repos'])} share a template; name them in "
                                  "Shared code and templates")
            for u in g["unresolved_hosts"]:
                if u["host"].split(":")[0] not in text:
                    warnings.append(f"{u['repo']} calls internal host {u['host']}, not matched to any repo; say what "
                                    "it is (Connections or Gaps)")
            for m2 in list(check_map.SECRET_LIKE.finditer(text)) + list(check_map.SECRET_ENV.finditer(text)):
                errors.append(f"secret-looking value copied into the system map: {m2.group(0)[:24]!r}…")
    for n in missing:
        errors.append(f"{n}: checkout missing")

    ok = not errors
    if not a.quiet or not ok:
        print(f"{'OK  ' if ok else 'FAIL'} workspace {ws} ({len(active)} repos, {len(g['edges'])} links, graph {g['hash']})")
        for e in errors:
            print(f"  error: {e}")
        for w in warnings:
            print(f"  warn:  {w}")
        print(f"\n{len(errors)} errors, {len(warnings)} warnings.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
