#!/usr/bin/env python3
"""Gate: is there a complete, current map of the codebase? Every other skill runs this first.

Usage: python3 check_map.py <repo_dir> [--map hiring/_repo/codebase-map.md] [--quiet]

Checks hiring/_repo/codebase-map.md against a fresh inventory of the repo:
  - all required sections exist and say something
  - every cited path (in `backticks`) exists in the repo
  - everything the inventory found is explained in the right section: each package or service, compose
    service, CI/CD pipeline file, deployment or IaC file, migration folder, API spec, auth or security code,
    data store, auth/security library, observability tool and test setup
  - the risks section is marked INTERNAL (never published)
  - no secret-looking values were copied into the map
  - the map is not stale: the structurally important files have not changed since it was written

Exit code 0 = map is complete and current, 1 = (re)build it with the map-codebase skill.
"""
import argparse
import io
import json
import re
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventory  # noqa: E402

SECTIONS = {
    "overview": r"overview|what (?:it|this) is",
    "components": r"components|services|architecture",
    "data": r"data(?: stores?| layer)?|database|schema",
    "apis": r"apis?|integrations|interfaces",
    "auth": r"auth\w*|security",
    "cicd": r"ci/?cd|pipelines?|build",
    "deploy": r"deploy\w*|infrastructure|hosting",
    "observability": r"observability|monitoring|logging",
    "testing": r"test\w*",
    "dependencies": r"dependencies|libraries",
    "conventions": r"conventions|code quality|standards",
    "risks": r"hot ?spots|risks|weak",
    "gaps": r"gaps|not covered|unknowns|limitations",
}
TITLES = {"overview": "Overview", "components": "Components and services", "data": "Data stores and schema",
          "apis": "APIs and integrations", "auth": "Authentication and security", "cicd": "CI/CD pipeline",
          "deploy": "Deployment and infrastructure", "observability": "Observability", "testing": "Testing",
          "dependencies": "Dependencies", "conventions": "Conventions", "risks": "Hot spots and risks (INTERNAL)",
          "gaps": "Gaps in this map"}
NEEDS_CITATION = {"components", "data", "apis", "auth", "cicd", "deploy", "observability", "testing",
                  "dependencies", "conventions", "risks"}
NONE_FOUND = re.compile(r"\bnone found\b|\bnot present\b|\bno [\w /-]+ (?:found|present|configured)\b", re.I)
SECRET_LIKE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\b(?:sk|pk|rk)_(?:live|test)_[0-9A-Za-z]{10,}|"
                         r"\bsk-[A-Za-z0-9]{20,}|\bgh[pousr]_[A-Za-z0-9]{30,}|\bxox[abpr]-[A-Za-z0-9-]{10,}|"
                         r"(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[\"']?[^\s\"'`]{6,}", re.I)
# Environment-variable assignments whose name says it holds a secret: JWT_SIGNING_KEY=..., DB_PASSWORD: ...
SECRET_ENV = re.compile(r"\b[A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|DSN|CREDENTIALS?|PRIVATE)\b\s*[:=]\s*"
                        r"[\"']?(?!\$\{|<|\[|str\b|None\b|null\b)[^\s\"'`]{6,}")

# inventory file category -> sections where at least one of those files (or its folder) must be cited
FILE_COVERAGE = {
    "ci_cd": ("cicd",),
    "deploy_infra": ("deploy",),
    "containers": ("deploy", "components"),
    "migrations": ("data",),
    "schema": ("data",),
    "api_specs": ("apis",),
    "auth_code": ("auth",),
    "security_files": ("auth", "conventions", "cicd"),
    "manifests": ("dependencies", "components"),
}
# detected label category -> sections that must name each label
LABEL_COVERAGE = {
    "data_stores": ("data",),
    "queues": ("components", "data"),
    "orm": ("data", "dependencies"),
    "auth_security": ("auth",),
    "observability": ("observability",),
    "proxies_gateways": ("deploy", "components"),
    "frameworks": ("overview", "components", "dependencies"),
    "test_frameworks": ("testing",),
}


def parse_sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = None
            for key, pat in SECTIONS.items():
                if key not in out and re.search(pat, m.group(1), re.I):
                    cur = key
                    out[key] = {"title": m.group(1), "body": []}
                    break
            continue
        if cur:
            out[cur]["body"].append(line)
    return {k: {"title": v["title"], "body": "\n".join(v["body"]).strip()} for k, v in out.items()}


def cited_paths(body):
    return [c.strip().rstrip("/") for c in re.findall(r"`([^`\n]+)`", body)
            if "/" in c or re.search(r"\.\w{1,6}$", c.strip()) or c.strip().startswith(".")]


def mentions(body, label):
    words = [w for w in re.split(r"[\s/()]+", label.lower()) if len(w) > 2 and w not in {"and", "the", "config"}]
    low = body.lower()
    return any(w in low for w in words) if words else label.lower() in low


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--map", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.repo).resolve()
    map_path = Path(args.map) if args.map else root / "hiring" / "_repo" / "codebase-map.md"
    errors, warnings = [], []

    if not map_path.exists():
        print(f"FAIL: no codebase map at {map_path}. Build it with the map-codebase skill first.")
        return 1
    text = map_path.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
        inventory.main([str(root), "--out", str(Path(tmp) / "inv.json")])
        inv = json.loads((Path(tmp) / "inv.json").read_text())

    # ---- staleness
    m = re.search(r"Inventory:\s*`?([0-9a-f]{12,64})", text)
    if not m:
        errors.append("header has no 'Inventory: <fingerprint>' line (copy it from inventory.json)")
    elif not inv["fingerprint"].startswith(m.group(1)):
        changed = ""
        saved = map_path.parent / "inventory.json"
        if saved.exists():
            old = json.loads(saved.read_text())
            diffs = []
            for k in set(old.get("files", {})) | set(inv["files"]):
                a, b = set(old.get("files", {}).get(k, [])), set(inv["files"].get(k, []))
                diffs += [f"+{x}" for x in sorted(b - a)] + [f"-{x}" for x in sorted(a - b)]
            if old.get("packages") != inv["packages"]:
                diffs.append("packages changed")
            old_k, new_k = old.get("key_files", {}), inv.get("key_files", {})
            diffs += [f"~{f}" for f in sorted(set(old_k) & set(new_k)) if old_k[f] != new_k[f]]
            changed = (" Changed: " + ", ".join(diffs[:8]) + (" …" if len(diffs) > 8 else "")) if diffs else \
                " Key files were edited (pipelines, manifests, migrations, deployment or auth code)."
        errors.append("STALE: the codebase changed since the map was written." + changed +
                      (" (+ added, - removed, ~ edited)" if changed.startswith(" Changed") else ""))
    mc = re.search(r"Commit:\s*`?([0-9a-f]{7,40}|none)", text)
    if inv.get("git_commit") and mc and mc.group(1) != "none" and not inv["git_commit"].startswith(mc.group(1)):
        warnings.append(f"map was written at commit {mc.group(1)[:10]}, repo is at {inv['git_commit'][:10]}")

    # ---- sections
    secs = parse_sections(text)
    for key, title in TITLES.items():
        if key not in secs:
            errors.append(f"missing section: ## {title}")
        elif len(secs[key]["body"]) < 20:
            errors.append(f"section '{secs[key]['title']}' is empty")
    for key in NEEDS_CITATION & set(secs):
        body = secs[key]["body"]
        if not cited_paths(body) and not NONE_FOUND.search(body):
            errors.append(f"section '{secs[key]['title']}' cites no files (cite `paths`, or say 'none found' and where you checked)")
    for key, sec in secs.items():
        for c in sorted(set(cited_paths(sec["body"]))):
            candidate = c.split(":")[0].split("#")[0].rstrip("*").rstrip("/")
            if "*" in candidate or not candidate:
                continue
            if not (root / candidate).exists():
                errors.append(f"section '{sec['title']}' cites `{c}`, which does not exist in the repo")
    if "risks" in secs and "INTERNAL" not in (secs["risks"]["title"] + secs["risks"]["body"][:300]):
        errors.append("the risks section must be marked INTERNAL (it must never be published)")
    for m2 in list(SECRET_LIKE.finditer(text)) + list(SECRET_ENV.finditer(text)):
        errors.append(f"secret-looking value copied into the map: {m2.group(0)[:24]!r}… (remove it)")

    # ---- coverage of what the inventory found
    def section_text(keys):
        return "\n".join(secs[k]["body"] for k in keys if k in secs)

    for cat, keys in FILE_COVERAGE.items():
        files = inv["files"].get(cat, [])
        if not files:
            continue
        body = section_text(keys)
        cited = set(cited_paths(body))
        hit = any(f in cited or any(f.startswith(c + "/") or c.startswith(f) for c in cited) or f in body for f in files)
        if not hit:
            where = " / ".join(TITLES[k] for k in keys)
            errors.append(f"inventory found {len(files)} {cat.replace('_', ' ')} file(s) (e.g. `{files[0]}`) but "
                          f"'{where}' doesn't cite any")
    if inv["files"].get("ci_cd"):
        body = section_text(("cicd",))
        uncovered = [f for f in inv["files"]["ci_cd"] if f not in body and Path(f).name not in body
                     and str(Path(f).parent) not in cited_paths(body)]
        if uncovered and len(uncovered) > len(inv["files"]["ci_cd"]) // 2:
            warnings.append(f"CI/CD section names only {len(inv['files']['ci_cd']) - len(uncovered)} of "
                            f"{len(inv['files']['ci_cd'])} pipeline files; summarise the rest (e.g. `.github/workflows/`)")
    for pkg in inv.get("packages", []):
        if pkg not in section_text(("components",)):
            errors.append(f"package/service `{pkg}` (has its own manifest) is not described in Components and services")
    for svc in inv.get("compose_services", []):
        if not re.search(rf"(?<![\w-]){re.escape(svc)}(?![\w-])", section_text(("components", "deploy"))):
            errors.append(f"compose service '{svc}' is not described in Components or Deployment")
    for cat, keys in LABEL_COVERAGE.items():
        body = section_text(keys)
        for label in inv["detected"].get(cat, []):
            if not mentions(body, label):
                where = " / ".join(TITLES[k] for k in keys)
                errors.append(f"inventory detected {label} ({cat.replace('_', ' ')}) but '{where}' doesn't mention it")
    if inv["size"]["test_files"] and "testing" in secs and not cited_paths(secs["testing"]["body"]):
        errors.append(f"{inv['size']['test_files']} test files exist but Testing cites none")
    if inv["files"].get("env_files"):
        body = section_text(("auth", "deploy", "risks"))
        if ".env" not in body:
            warnings.append("env files exist (contents never read); note how configuration and secrets are handled")

    ok = not errors
    if not args.quiet or not ok:
        print(f"{'OK  ' if ok else 'FAIL'} codebase map {map_path}")
        for e in errors:
            print(f"  error: {e}")
        for w in warnings:
            print(f"  warn:  {w}")
        print(f"\n{len(errors)} errors, {len(warnings)} warnings.")
        if not ok:
            print("Fix the map (or rebuild it with the map-codebase skill) before writing job descriptions, rubrics, "
                  "screening or interview kits.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
