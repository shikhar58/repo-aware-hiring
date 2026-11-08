#!/usr/bin/env python3
"""Build the cross-repo graph of a hiring workspace from each repo's inventory. Deterministic, no model.

Usage: python3 system_graph.py <workspace> [--fresh]

Reads maps/<repo>/inventory.json (run `workspace.py scan` first, or pass --fresh to re-inventory every repo) and finds:
  package   repo A depends on a package that repo B publishes (pyproject/package.json/go.mod/pom/Cargo names)
  image     repo A deploys a container image that repo B builds (CI `docker build/push`, compose build + image)
  http      repo A calls an internal host that resolves to repo B (B's name, B's image name, or a k8s Service)
  contract  repos A and B contain the same API contract (same proto package or OpenAPI title)
and groups repos that look generated from the same template (similar folder layout and frameworks), so one full
map can explain the shared structure.

Writes system/system-graph.json and system/system-graph.md (Mermaid diagram, edge table, unresolved hosts).
system-map.md, written by the agent, must carry the graph's hash: `Graph: <hash>` (check_system.py enforces it).
"""
import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
from contextlib import redirect_stdout
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "map-codebase" / "scripts"))
import wslib  # noqa: E402

SUFFIXES = ("-service", "-svc", "-api", "-app", "-server", "-backend", "_service", "_svc", "-worker")
TEMPLATE_SIMILARITY = 0.6


def norm_pkg(name):
    return re.sub(r"[-_.]+", "-", name.lower()).strip("-")


def pkg_match(dep, pub):
    if norm_pkg(dep) == norm_pkg(pub):
        return True
    if "/" in pub and not pub.startswith("@"):            # Go module path vs last segment
        return dep == pub or pub.endswith("/" + dep) or norm_pkg(pub.rsplit("/", 1)[-1]) == norm_pkg(dep)
    return False


def name_aliases(name):
    out = {name.lower()}
    for s in SUFFIXES:
        if name.lower().endswith(s):
            out.add(name.lower()[: -len(s)])
    return {a for a in out if a}


def image_short(img):
    return img.rsplit("/", 1)[-1]


def load_inventories(ws, data, fresh=False):
    import inventory  # noqa: E402
    invs, missing = {}, []
    for r in wslib.active_repos(data):
        path = wslib.repo_path(ws, r)
        saved = wslib.map_dir(ws, r["name"]) / "inventory.json"
        if not path.is_dir():
            missing.append(r["name"])
            continue
        if fresh or not saved.exists():
            with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
                out = Path(tmp) / "inv.json"
                inventory.main([str(path), "--out", str(out)])
                inv = json.loads(out.read_text())
            if not fresh:
                saved.parent.mkdir(parents=True, exist_ok=True)
                saved.write_text(json.dumps(inv, indent=2) + "\n")
        else:
            inv = json.loads(saved.read_text())
        invs[r["name"]] = inv
    return invs, missing


def build(data, invs):
    repos = [r for r in wslib.active_repos(data) if r["name"] in invs]
    names = [r["name"] for r in repos]
    tiers = {r["name"]: r.get("tier") for r in repos}
    L = {n: invs[n].get("links", {}) for n in names}
    edges = []

    def add(kind, a, b, detail, evidence):
        e = {"kind": kind, "from": a, "to": b, "detail": detail, "evidence": evidence}
        if e not in edges:
            edges.append(e)

    # package
    for a in names:
        for b in names:
            if a == b:
                continue
            for manifest, pub in L[b].get("published", {}).items():
                for dep in L[a].get("dependencies", []):
                    if pkg_match(dep, pub):
                        add("package", a, b, f"depends on {pub}",
                            [f"{b}:{manifest}"] + [f"{a}:{m}" for m in invs[a]["files"].get("manifests", [])[:3]])
    # image
    built = {n: L[n].get("images_built", {}) for n in names}
    for a in names:
        for img, files in L[a].get("images_deployed", {}).items():
            for b in names:
                if b == a:
                    continue
                for bimg, bfiles in built[b].items():
                    exact = img == bimg
                    loose = image_short(img) == image_short(bimg) and ("$" in img or "$" in bimg or "/" not in img
                                                                      or "/" not in bimg)
                    if exact or loose:
                        add("image", a, b, f"deploys image {img}" + ("" if exact else f" (built as {bimg})"),
                            [f"{a}:{f}" for f in files[:2]] + [f"{b}:{f}" for f in bfiles[:2]])
    # http
    owner = {}
    for b in names:
        for al in name_aliases(b):
            owner.setdefault(al, b)
        for img in built[b]:
            owner.setdefault(image_short(img), b)
    declared_by = {}
    for n in names:
        for s in L[n].get("service_names", []):
            declared_by.setdefault(s, n)
    unresolved = []
    for a in names:
        for host, files in L[a].get("internal_hosts", {}).items():
            h = host.split(":")[0].lower()
            label = h.split(".")[0]
            b = owner.get(h) or owner.get(label)
            if b and b != a:
                via = ""
                if label in declared_by and declared_by[label] not in (a, b):
                    via = f" (Service declared in {declared_by[label]})"
                add("http", a, b, f"calls http://{host}{via}", [f"{a}:{f}" for f in files[:3]])
            elif not b and label not in {s.lower() for s in invs[a].get("compose_services", [])}:
                unresolved.append({"repo": a, "host": host, "files": files[:3],
                                   "declared_in": declared_by.get(label)})
    # contracts
    for a, b in combinations(names, 2):
        for spec in sorted(set(L[a].get("specs", {})) & set(L[b].get("specs", {}))):
            add("contract", a, b, f"share contract {spec}",
                [f"{a}:{f}" for f in L[a]["specs"][spec][:2]] + [f"{b}:{f}" for f in L[b]["specs"][spec][:2]])

    # templates (union-find over similar layouts)
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    sims = {}
    for a, b in combinations(names, 2):
        la, lb = set(invs[a].get("layout", [])), set(invs[b].get("layout", []))
        if not la or not lb or not invs[a]["size"]["source_files"] or not invs[b]["size"]["source_files"]:
            continue
        j = len(la & lb) / len(la | lb)
        fa = set(invs[a]["detected"].get("frameworks", []))
        fb = set(invs[b]["detected"].get("frameworks", []))
        if j >= TEMPLATE_SIMILARITY and fa == fb:
            sims[(a, b)] = round(j, 2)
            parent[find(a)] = find(b)
    groups = {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    templates = []
    for members in groups.values():
        if len(members) > 1:
            pair_s = [s for (a, b), s in sims.items() if a in members and b in members]
            shared = set.intersection(*(set(invs[m].get("layout", [])) for m in members))
            templates.append({"repos": sorted(members), "similarity": min(pair_s),
                              "shared_layout": sorted(shared)[:15],
                              "frameworks": invs[members[0]]["detected"].get("frameworks", [])})

    # roles in the system
    roles = {}
    for n in names:
        r = []
        if any(e["kind"] == "package" and e["to"] == n for e in edges) or L[n].get("published") and not built[n]:
            r.append("library")
        if built[n]:
            r.append("service")
        if L[n].get("images_deployed") and any(e["kind"] == "image" and e["from"] == n for e in edges):
            r.append("deploys others")
        if not r:
            r.append("service" if invs[n]["size"]["source_files"] else "config/other")
        roles[n] = r

    digest = hashlib.sha256(json.dumps({"repos": sorted((n, tiers[n]) for n in names),
                                        "edges": sorted(json.dumps(e, sort_keys=True) for e in edges),
                                        "templates": [t["repos"] for t in templates]},
                                       sort_keys=True).encode()).hexdigest()[:16]
    return {"generated_at": wslib.now(), "hash": digest,
            "repos": [{"name": n, "tier": tiers[n], "role": roles[n],
                       "commit": invs[n].get("git_commit"), "fingerprint": invs[n]["fingerprint"][:16]} for n in names],
            "edges": edges, "unresolved_hosts": unresolved, "templates": templates}


def mermaid_id(n):
    return re.sub(r"[^A-Za-z0-9_]", "_", n)


def render_md(g):
    out = ["# System graph (generated, do not edit)", f"Graph: {g['hash']} · Generated: {g['generated_at']}", "",
           "```mermaid", "flowchart LR"]
    for r in g["repos"]:
        shape = ("[(", ")]") if "library" in r["role"] else ("[/", "/]") if "deploys others" in r["role"] else ("[", "]")
        out.append(f"  {mermaid_id(r['name'])}{shape[0]}\"{r['name']}<br/>{r['tier']}\"{shape[1]}")
    arrow = {"package": "-- uses lib -->", "image": "-- deploys -->", "http": "-- calls -->", "contract": "<-- contract -->"}
    for e in g["edges"]:
        out.append(f"  {mermaid_id(e['from'])} {arrow[e['kind']]} {mermaid_id(e['to'])}")
    out += ["```", "", "| From | Kind | To | Detail | Evidence |", "|---|---|---|---|---|"]
    for e in g["edges"]:
        out.append(f"| {e['from']} | {e['kind']} | {e['to']} | {e['detail']} | " + ", ".join(f"`{x}`" for x in e["evidence"]) + " |")
    if not g["edges"]:
        out.append("| – | – | – | no links found between these repos | – |")
    if g["templates"]:
        out += ["", "## Same template"]
        for t in g["templates"]:
            out.append(f"- {', '.join(t['repos'])}: layout similarity {t['similarity']}, frameworks "
                       f"{', '.join(t['frameworks']) or 'none'}. Map the shared structure once; describe only differences.")
    if g["unresolved_hosts"]:
        out += ["", "## Internal hosts not matched to a repo in the workspace"]
        for u in g["unresolved_hosts"]:
            out.append(f"- {u['repo']} calls `{u['host']}` ({', '.join(u['files'])})"
                       + (f"; a Service with that name is declared in {u['declared_in']}" if u["declared_in"] else
                          "; maybe a repo that isn't in the workspace, or an external dependency"))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ws")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args(argv)
    ws = wslib.find_workspace(a.ws)
    if not ws:
        print(f"FAIL: no workspace at {a.ws}")
        return 1
    data = wslib.load(ws)
    invs, missing = load_inventories(ws, data, fresh=a.fresh)
    g = build(data, invs)
    sysdir = ws / "system"
    sysdir.mkdir(exist_ok=True)
    (sysdir / "system-graph.json").write_text(json.dumps(g, indent=2) + "\n")
    (sysdir / "system-graph.md").write_text(render_md(g))
    print(f"System graph {g['hash']}: {len(g['repos'])} repos, {len(g['edges'])} links -> {sysdir / 'system-graph.md'}")
    for e in g["edges"]:
        print(f"  {e['from']} -[{e['kind']}]-> {e['to']}: {e['detail']}")
    for t in g["templates"]:
        print(f"  same template: {', '.join(t['repos'])} (similarity {t['similarity']})")
    for u in g["unresolved_hosts"]:
        print(f"  unresolved host: {u['repo']} calls {u['host']}")
    for m in missing:
        print(f"  MISSING checkout: {m}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
