#!/usr/bin/env python3
"""Manage a multi-repo hiring workspace: a private folder that references or clones the repos a hire will work on.

Usage:
  workspace.py init   <ws> [--name NAME]
  workspace.py add    <ws> <local-path | https-or-ssh-git-url | owner/repo> [--name N] [--tier primary|supporting]
                      [--ref BRANCH]
  workspace.py tier   <ws> <repo> primary|supporting|ignored
  workspace.py remove <ws> <repo>
  workspace.py list   <ws>
  workspace.py scan   <ws>            inventory every active repo into maps/<repo>/inventory.json, then build the system graph
  workspace.py status <ws>            what is mapped, what is stale, what is missing
  workspace.py sync   <ws>            pull clones (fast-forward only), then scan
  workspace.py new-role <ws> <role>   create roles/<role>/ with focus.md and decisions.json

Local paths are referenced, never copied or modified. URLs are cloned into <ws>/repos/ (shallow). URLs containing
credentials are refused: use your git credential helper or SSH keys instead.
Exit code 0 = ok, 1 = something needs attention (status) or failed.
"""
import argparse
import io
import re
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "map-codebase" / "scripts"))
import wslib  # noqa: E402

GIT_URL = re.compile(r"^(https://[\w.-]+(:\d+)?/[\w./~-]+?|ssh://git@[\w.-]+(:\d+)?/[\w./~-]+?|git@[\w.-]+:[\w./~-]+?)(\.git)?/?$")
SHORTHAND = re.compile(r"^[A-Za-z0-9][\w.-]*/[\w.-]+$")
CREDS = re.compile(r"^https?://[^/@]+@")

FOCUS_TEMPLATE = """# Focus for this role
<!-- Optional. Tell every step what to concentrate on, in plain words. Examples:
     "Focus on the payment library and how checkout and billing use it; the hire will own payments."
     "Mostly the data pipeline in ingest-svc; frontend repos matter only for context."
     Describe the WORK, not the person: criteria about age, gender, nationality, schools, family or
     similar are rejected by focus.py check. The focus can't switch off redaction, evidence checks or the rubric. -->
"""


def git(*args, cwd=None, timeout=600):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)


def cmd_init(ws, name):
    ws.mkdir(parents=True, exist_ok=True)
    if (ws / wslib.WS_FILE).exists():
        print(f"Workspace already exists at {ws}")
        return 0
    for d in ("repos", "maps", "system", "roles"):
        (ws / d).mkdir(exist_ok=True)
    wslib.save(ws, {"version": 1, "name": name or ws.name, "created": wslib.now(), "repos": []})
    (ws / ".gitignore").write_text("# This workspace holds candidate data and internal maps. Never commit it.\n*\n")
    (ws / "decisions.json").write_text("[]\n")
    print(f"Created workspace {ws}\n  next: workspace.py add {ws} <path or git URL> --tier primary")
    return 0


def _inside(child, parent):
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def cmd_add(ws, source, name, tier, ref):
    data = wslib.load(ws)
    src = source.strip()
    if CREDS.match(src):
        print("FAIL: the URL contains credentials. Remove them and use a git credential helper or SSH key instead.")
        return 1
    local = Path(src).expanduser()
    if local.is_dir():
        local = local.resolve()
        if _inside(ws, local):
            print(f"FAIL: the workspace {ws} is inside {local}. Put the workspace outside the repos so candidate data "
                  "can never be committed with the code.")
            return 1
        repo = {"name": wslib.slug(name or local.name), "kind": "local", "path": str(local), "source": str(local)}
        if not (local / ".git").exists():
            print(f"  note: {local} is not a git checkout; staleness will rely on file hashes only")
    else:
        url = src
        if SHORTHAND.match(src) and not src.startswith((".", "/", "~")):
            url = f"https://github.com/{src}.git"
        if not GIT_URL.match(url):
            print(f"FAIL: {src!r} is neither an existing folder nor a git URL (https://…, git@…:…, ssh://… or owner/repo)")
            return 1
        base = re.sub(r"\.git/?$", "", url.rstrip("/")).rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        repo = {"name": wslib.slug(name or base), "kind": "clone", "source": url}
        if ref:
            repo["ref"] = ref
    if not wslib.SLUG.match(repo["name"]):
        print(f"FAIL: invalid repo name {repo['name']!r}")
        return 1
    if any(r["name"] == repo["name"] for r in data["repos"]):
        print(f"FAIL: a repo named {repo['name']} is already in the workspace (use --name to pick another)")
        return 1
    if repo["kind"] == "clone":
        dest = ws / "repos" / repo["name"]
        args = ["clone", "--depth", "1"] + (["--branch", ref] if ref else []) + [repo["source"], str(dest)]
        r = git(*args)
        if r.returncode != 0:
            print(f"FAIL: git clone failed:\n{r.stderr.strip()[-600:]}\n"
                  "If the repo is private, make sure your git credentials or SSH key can read it, or clone it "
                  "yourself and add the local path.")
            return 1
    repo["tier"] = tier or ("primary" if not data["repos"] else "supporting")
    repo["added"] = wslib.now()
    data["repos"].append(repo)
    wslib.save(ws, data)
    print(f"Added {repo['name']} ({repo['kind']}, tier {repo['tier']}) -> {wslib.repo_path(ws, repo)}")
    return 0


def cmd_tier(ws, name, tier):
    data = wslib.load(ws)
    for r in data["repos"]:
        if r["name"] == name:
            r["tier"] = tier
            wslib.save(ws, data)
            print(f"{name}: tier {tier} (map needed: "
                  f"{'full codebase map' if tier == 'primary' else 'service card' if tier == 'supporting' else 'none'})")
            return 0
    print(f"FAIL: no repo named {name}")
    return 1


def cmd_remove(ws, name):
    data = wslib.load(ws)
    keep = [r for r in data["repos"] if r["name"] != name]
    if len(keep) == len(data["repos"]):
        print(f"FAIL: no repo named {name}")
        return 1
    data["repos"] = keep
    wslib.save(ws, data)
    print(f"Removed {name} from the workspace (its clone and map, if any, are left on disk; delete them by hand)")
    return 0


def cmd_list(ws):
    data = wslib.load(ws)
    print(f"Workspace {data.get('name')} ({ws})")
    if not data["repos"]:
        print("  no repos yet")
    for r in data["repos"]:
        print(f"  {r['name']:<24} {r['tier']:<10} {r['kind']:<5} {r['source']}")
    roles = sorted(p.name for p in (ws / "roles").glob("*") if p.is_dir()) if (ws / "roles").exists() else []
    print(f"  roles: {', '.join(roles) or 'none'}")
    return 0


def cmd_scan(ws):
    import inventory  # noqa: E402
    import system_graph  # noqa: E402
    data = wslib.load(ws)
    ok = True
    for r in wslib.active_repos(data):
        path = wslib.repo_path(ws, r)
        if not path.is_dir():
            print(f"  MISSING {r['name']}: {path} does not exist")
            ok = False
            continue
        out = wslib.map_dir(ws, r["name"]) / "inventory.json"
        with redirect_stdout(io.StringIO()) as buf:
            inventory.main([str(path), "--out", str(out)])
        lines = buf.getvalue().splitlines()
        print(f"  scanned {r['name']} ({r['tier']}): " + (lines[1].strip() if len(lines) > 1 else ""))
        for ln in lines:
            if ln.strip().startswith("links:"):
                print("    " + ln.strip())
    system_graph.main([str(ws)])
    return 0 if ok else 1


def cmd_status(ws):
    import check_map  # noqa: E402
    import check_system  # noqa: E402
    data = wslib.load(ws)
    problems = 0
    print(f"Workspace {data.get('name')} ({ws})")
    for r in data["repos"]:
        if r["tier"] == "ignored":
            print(f"  -    {r['name']:<24} ignored")
            continue
        path = wslib.repo_path(ws, r)
        mp = wslib.map_file(ws, r)
        level = "full" if r["tier"] == "primary" else "card"
        if not path.is_dir():
            print(f"  FAIL {r['name']:<24} checkout missing at {path}")
            problems += 1
            continue
        with redirect_stdout(io.StringIO()) as buf:
            rc = check_map.main([str(path), "--map", str(mp), "--level", level, "--quiet"])
        errs = [ln.strip()[7:] for ln in buf.getvalue().splitlines() if ln.strip().startswith("error:")]
        label = "codebase map" if level == "full" else "service card"
        if rc == 0:
            print(f"  OK   {r['name']:<24} {r['tier']:<10} {label} current")
        else:
            problems += 1
            why = "missing" if not mp.exists() else ("STALE" if any("STALE" in e for e in errs) else f"{len(errs)} problem(s)")
            print(f"  FAIL {r['name']:<24} {r['tier']:<10} {label} {why}: {mp}")
            for e in errs[:3]:
                print(f"         - {e[:160]}")
    with redirect_stdout(io.StringIO()) as buf:
        rc = check_system.main([str(ws), "--quiet", "--skip-maps"])
    if rc == 0:
        print("  OK   system map current")
    else:
        problems += 1
        print("  FAIL system map: " + "; ".join(ln.strip()[7:] for ln in buf.getvalue().splitlines()
                                                if ln.strip().startswith("error:"))[:400])
    print(f"\n{problems} thing(s) need attention." if problems else "\nEverything is mapped and current.")
    return 1 if problems else 0


def cmd_sync(ws):
    data = wslib.load(ws)
    for r in data["repos"]:
        if r["kind"] != "clone" or r["tier"] == "ignored":
            continue
        path = wslib.repo_path(ws, r)
        res = git("pull", "--ff-only", cwd=path)
        print(f"  {r['name']}: " + (res.stdout.strip().splitlines()[-1] if res.returncode == 0 and res.stdout.strip()
                                     else "pull failed: " + res.stderr.strip()[-200:]))
    return cmd_scan(ws)


def cmd_new_role(ws, role):
    role = wslib.slug(role)
    d = ws / "roles" / role
    d.mkdir(parents=True, exist_ok=True)
    if not (d / "focus.md").exists():
        (d / "focus.md").write_text(FOCUS_TEMPLATE, encoding="utf-8")
    if not (d / "decisions.json").exists():
        (d / "decisions.json").write_text("[]\n")
    print(f"Role folder {d}\n  write the focus (optional) in {d / 'focus.md'}, then run the hiring-plan skill")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("ws"); p.add_argument("--name")
    p = sub.add_parser("add"); p.add_argument("ws"); p.add_argument("source"); p.add_argument("--name")
    p.add_argument("--tier", choices=wslib.TIERS[:2]); p.add_argument("--ref")
    p = sub.add_parser("tier"); p.add_argument("ws"); p.add_argument("repo"); p.add_argument("tier", choices=wslib.TIERS)
    p = sub.add_parser("remove"); p.add_argument("ws"); p.add_argument("repo")
    for c in ("list", "scan", "status", "sync"):
        sub.add_parser(c).add_argument("ws")
    p = sub.add_parser("new-role"); p.add_argument("ws"); p.add_argument("role")
    a = ap.parse_args(argv)
    ws = Path(a.ws).expanduser().resolve()
    if a.cmd == "init":
        return cmd_init(ws, a.name)
    if not (ws / wslib.WS_FILE).exists():
        print(f"FAIL: no workspace at {ws} (create it with: workspace.py init {ws})")
        return 1
    sys.path.insert(0, str(HERE))
    return {"add": lambda: cmd_add(ws, a.source, a.name, a.tier, a.ref), "tier": lambda: cmd_tier(ws, a.repo, a.tier),
            "remove": lambda: cmd_remove(ws, a.repo), "list": lambda: cmd_list(ws), "scan": lambda: cmd_scan(ws),
            "status": lambda: cmd_status(ws), "sync": lambda: cmd_sync(ws),
            "new-role": lambda: cmd_new_role(ws, a.role)}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
