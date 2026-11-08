#!/usr/bin/env python3
"""Trace where a library is defined and how every repo uses it: declarations, imports and call sites with file:line.

Usage:
  trace_usage.py <workspace-or-repo> <library> [--out usage.md] [--json usage.json] [--max-sites 30]

<library> can be a package name (acme-payments, @acme/payments), a module (acme_payments), a Go module path,
a Java/Kotlin package (com.acme.payments), or, in a workspace, the name of the repo that defines it.
Languages: Python, TypeScript/JavaScript, Go, Java/Kotlin. Deterministic, standard library only; it reads source
and manifest files, never env files. Use it when the focus names a library, so job descriptions, rubrics and
interview questions are grounded in how the library is really used, not guessed.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "map-codebase" / "scripts"))
import inventory  # noqa: E402
import wslib  # noqa: E402

SRC = {".py": "py", ".ts": "js", ".tsx": "js", ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js",
       ".go": "go", ".java": "java", ".kt": "java"}
MANIFEST_NAMES = re.compile(r"^(requirements[\w.-]*\.txt|pyproject\.toml|setup\.cfg|setup\.py|Pipfile|package\.json|"
                            r"go\.mod|pom\.xml|build\.gradle(\.kts)?)$")


def files(root, exclude=None):
    for p in inventory.walk(root):
        rel = p.relative_to(root).as_posix()
        if inventory.ENV_FILES.search(rel):
            continue
        if exclude and (rel + "/").startswith(exclude):
            continue
        if p.suffix in SRC or MANIFEST_NAMES.match(p.name):
            yield p, rel


def text_of(p):
    return inventory.read(p, 1_000_000)


# ------------------------------------------------------------------ resolve what to look for
def resolve(target_root, ctx, library):
    """Return (defining_repo_name or None, defining_root or None, sub_dir prefix or None, ids)."""
    lib = library.strip()
    ids = {"pkg": {lib.lower()}, "py": set(), "js": set(), "go": set(), "java": set()}
    def_name, def_root, prefix = None, None, None
    candidates = ctx.maps() if ctx.mode == "workspace" else []
    for name, path, _m, _l in candidates:
        inv_path = Path(ctx.ws) / "maps" / name / "inventory.json"
        pubs = set()
        if inv_path.exists():
            pubs = set(json.loads(inv_path.read_text()).get("links", {}).get("published", {}).values())
        if name.lower() == lib.lower() or lib.lower() in pubs or \
                any(re.sub(r"[-_.]", "", p) == re.sub(r"[-_.]", "", lib.lower()) for p in pubs):
            def_name, def_root = name, path
            if pubs and lib.lower() not in pubs:
                ids["pkg"] = set(pubs)   # looked up by repo name: search for what it publishes
            else:
                ids["pkg"] |= pubs
            break
    if def_root is None and ctx.mode == "single":
        # a library inside a monorepo: a folder whose manifest publishes it, or a folder named like the module
        for p, rel in files(target_root):
            if MANIFEST_NAMES.match(p.name):
                pub = inventory.published_name(p, text_of(p))
                if pub and re.sub(r"[-_.]", "", pub) == re.sub(r"[-_.]", "", lib.lower()):
                    prefix = str(Path(rel).parent) + "/" if str(Path(rel).parent) != "." else None
                    def_root = target_root / Path(rel).parent
                    ids["pkg"].add(pub)
                    break
    if def_root is None and ctx.mode == "single" and re.fullmatch(r"[a-z][\w]*(\.[a-z_][\w]*)+", lib):
        for p, rel in files(target_root):          # Java/Kotlin: the folder whose sources declare that package
            if p.suffix in (".java", ".kt") and re.search(rf"^package\s+{re.escape(lib)}(\.|\s*;|\s*$)", text_of(p), re.M):
                top = rel.split("src/")[0] if "src/" in rel else str(Path(rel).parent) + "/"
                prefix = top if top not in ("", "./") else None
                def_root = target_root / top if prefix else target_root
                break
    for pkg in list(ids["pkg"]):
        base = pkg.split("/")[-1] if not pkg.startswith("@") else pkg
        ids["py"].add(re.sub(r"[-.]", "_", base.lower()))
        ids["js"].add(pkg)
        if "/" in pkg and "." in pkg.split("/")[0]:
            ids["go"].add(pkg)
        if re.fullmatch(r"[a-z][\w]*(\.[a-z_][\w]*)+", pkg) and "_" not in pkg:
            ids["java"].add(pkg)
    if def_root:
        for p, rel in files(def_root):
            t = text_of(p)
            if p.name == "__init__.py":
                parts = Path(rel).parts
                if len(parts) >= 2 and parts[-2] not in ("tests", "test"):
                    pkg_dir = parts[-2]
                    if (len(parts) == 2) or parts[0] in ("src", "lib", "python"):
                        ids["py"].add(pkg_dir)
            if p.name == "go.mod":
                m = re.search(r"^module\s+(\S+)", t, re.M)
                if m:
                    ids["go"].add(m.group(1))
            if p.suffix in (".java", ".kt"):
                m = re.search(r"^package\s+([\w.]+)", t, re.M)
                if m:
                    ids["java"].add(".".join(m.group(1).split(".")[:3]))
    return def_name, def_root, prefix, ids


def exports(def_root, ids, prefix=None):
    out = defaultdict(list)  # symbol -> [file:line]
    if not def_root:
        return out
    for p, rel in files(def_root):
        if re.search(r"(^|/)(tests?|__tests__|examples?)/", rel):
            continue
        lang = SRC.get(p.suffix)
        t = text_of(p)
        loc = (prefix or "") + rel
        if lang == "py" and any(f"/{m}/" in f"/{rel}" for m in ids["py"]):
            for i, ln in enumerate(t.splitlines(), 1):
                m = re.match(r"(?:async\s+)?(?:def|class)\s+([A-Za-z]\w*)", ln)
                if m:
                    out[m.group(1)].append(f"{loc}:{i}")
        elif lang == "js":
            for i, ln in enumerate(t.splitlines(), 1):
                m = re.match(r"\s*export\s+(?:default\s+)?(?:async\s+)?(?:function\*?|class|const|let|interface|type|enum)\s+(\w+)", ln)
                if m:
                    out[m.group(1)].append(f"{loc}:{i}")
        elif lang == "go":
            for i, ln in enumerate(t.splitlines(), 1):
                m = re.match(r"func\s+(?:\([^)]*\)\s*)?([A-Z]\w*)|type\s+([A-Z]\w*)", ln)
                if m:
                    out[m.group(1) or m.group(2)].append(f"{loc}:{i}")
        elif lang == "java":
            for i, ln in enumerate(t.splitlines(), 1):
                m = re.match(r"\s*public\s+(?:final\s+|abstract\s+)*(?:class|interface|enum|record)\s+(\w+)", ln)
                if m:
                    out[m.group(1)].append(f"{loc}:{i}")
    return out


# ------------------------------------------------------------------ find usage in one repo
def py_imports(t, mods):
    """-> (import_lines, {local_name: qualified}, namespace_aliases)"""
    lines, names, ns = [], {}, set()
    alt = "|".join(re.escape(m) for m in sorted(mods, key=len, reverse=True))
    if not alt:
        return lines, names, ns
    for m in re.finditer(rf"^[ \t]*import\s+((?:{alt})(?:\.\w+)*)(?:\s+as\s+(\w+))?", t, re.M):
        lines.append((t[:m.start()].count("\n") + 1, m.group(0).strip()))
        ns.add(m.group(2) or m.group(1))
    for m in re.finditer(rf"^[ \t]*from\s+((?:{alt})(?:\.\w+)*)\s+import\s+(\([^)]*\)|[^\n]+)", t, re.M):
        lines.append((t[:m.start()].count("\n") + 1, " ".join(m.group(0).split())))
        for part in re.sub(r"[()\n\\]", " ", m.group(2)).split(","):
            bits = part.split("#")[0].split()
            if not bits:
                continue
            if len(bits) >= 3 and bits[1] == "as":
                names[bits[2]] = bits[0]
            elif bits[0] != "*":
                names[bits[0]] = bits[0]
    return lines, names, ns


def js_imports(t, pkgs):
    lines, names, ns = [], {}, set()
    alt = "|".join(re.escape(p) for p in sorted(pkgs, key=len, reverse=True))
    if not alt:
        return lines, names, ns
    for m in re.finditer(rf"import\s+([^;]*?)\s+from\s+[\"']((?:{alt})(?:/[^\"']*)?)[\"']", t):
        lines.append((t[:m.start()].count("\n") + 1, " ".join(m.group(0).split())[:160]))
        clause = m.group(1)
        mm = re.search(r"\*\s+as\s+(\w+)", clause)
        if mm:
            ns.add(mm.group(1))
        braces = re.search(r"\{([^}]*)\}", clause)
        if braces:
            for part in braces.group(1).split(","):
                bits = part.split()
                if bits:
                    names[bits[-1]] = bits[0]
        default = re.match(r"\s*(\w+)\s*(?:,|$)", clause)
        if default and default.group(1) != "type":
            ns.add(default.group(1))
    for m in re.finditer(rf"(?:const|let|var)\s+(\{{[^}}]*\}}|\w+)\s*=\s*require\(\s*[\"']((?:{alt})(?:/[^\"']*)?)[\"']\s*\)", t):
        lines.append((t[:m.start()].count("\n") + 1, " ".join(m.group(0).split())[:160]))
        if m.group(1).startswith("{"):
            for part in m.group(1).strip("{}").split(","):
                bits = [b for b in re.split(r"[\s:]+", part) if b]
                if bits:
                    names[bits[-1]] = bits[0]
        else:
            ns.add(m.group(1))
    return lines, names, ns


def go_imports(t, mods):
    lines, ns = [], set()
    for m in re.finditer(r"^\s*(?:import\s+)?(\w+\s+)?\"([^\"]+)\"", t, re.M):
        path = m.group(2)
        if any(path == mod or path.startswith(mod + "/") for mod in mods):
            lines.append((t[:m.start()].count("\n") + 1, " ".join(m.group(0).split())))
            ns.add((m.group(1) or "").strip() or path.rsplit("/", 1)[-1].replace("-", "_"))
    return lines, {}, ns


def java_imports(t, pkgs, exported):
    lines, names = [], {}
    for m in re.finditer(r"^\s*import\s+(?:static\s+)?([\w.]+)(\.\*)?\s*;?", t, re.M):
        q = m.group(1)
        if any(q == p or q.startswith(p + ".") for p in pkgs):
            lines.append((t[:m.start()].count("\n") + 1, m.group(0).strip()))
            if m.group(2):
                names.update({s: s for s in exported})
            else:
                names[q.rsplit(".", 1)[-1]] = q.rsplit(".", 1)[-1]
    return lines, names, set()


def declarations(root, pkgs, exclude=None):
    out = []
    for p, rel in files(root, exclude):
        if not MANIFEST_NAMES.match(p.name):
            continue
        for i, ln in enumerate(text_of(p).splitlines(), 1):
            low = ln.lower()
            for pkg in pkgs:
                short = pkg.rsplit("/", 1)[-1] if "/" in pkg and not pkg.startswith("@") else pkg
                if re.search(rf"(?<![\w.@/-]){re.escape(pkg)}(?![\w-])", low) or \
                        (p.name == "pom.xml" and f"<artifactid>{short}</artifactid>" in low.replace(" ", "")):
                    if p.name in ("pyproject.toml", "package.json", "setup.py", "setup.cfg") and \
                            re.match(r"\s*\"?name\"?\s*[:=]", ln):
                        continue  # the library's own name line
                    out.append({"file": f"{rel}:{i}", "line": ln.strip()[:120]})
                    break
    return out


def trace_repo(root, ids, exported, exclude=None, max_sites=30):
    res = {"declared": declarations(root, ids["pkg"], exclude), "imports": [], "calls": defaultdict(list)}
    for p, rel in files(root, exclude):
        lang = SRC.get(p.suffix)
        if not lang:
            continue
        t = text_of(p)
        if lang == "py":
            imp, names, ns = py_imports(t, ids["py"])
        elif lang == "js":
            imp, names, ns = js_imports(t, ids["js"])
        elif lang == "go":
            imp, names, ns = go_imports(t, ids["go"])
        else:
            imp, names, ns = java_imports(t, ids["java"], exported)
        if not imp:
            continue
        res["imports"] += [{"file": f"{rel}:{n}", "line": line} for n, line in imp]
        import_lines = {n for n, _ in imp}
        for i, ln in enumerate(t.splitlines(), 1):
            if i in import_lines or ln.lstrip().startswith(("#", "//", "import ", "from ")):
                continue
            for local, orig in names.items():
                if re.search(rf"(?<![\w.]){re.escape(local)}\s*[(.<]|new\s+{re.escape(local)}\b|"
                             rf"(?<![\w.]){re.escape(local)}\s+\w+\s*[=;)]", ln):
                    res["calls"][orig].append(f"{rel}:{i}")
            for alias in ns:
                for sym in re.findall(rf"(?<![\w.]){re.escape(alias)}\.(\w+)", ln):
                    res["calls"][sym].append(f"{rel}:{i}")
    res["calls"] = {k: v[:max_sites] for k, v in sorted(res["calls"].items(), key=lambda kv: (-len(kv[1]), kv[0]))}
    return res


def render(lib, def_name, def_loc, ids, exported, per_repo):
    out = [f"# How `{lib}` is used", ""]
    if def_loc:
        out.append(f"Defined in **{def_name or def_loc}**. Import names: "
                   + ", ".join(f"`{x}`" for x in sorted(ids["py"] | ids["go"] | ids["java"] | ids["js"])) + ".")
        if exported:
            out.append(f"Public symbols ({len(exported)}): " + ", ".join(
                f"`{s}` ({v[0]})" for s, v in sorted(exported.items())[:25]) + (" …" if len(exported) > 25 else ""))
    else:
        out.append("Definition not found in the scanned repos (third-party or not in the workspace); showing usage only.")
    used_any = set()
    out += ["", "| Repo | Declared | Import sites | Symbols used | Call sites |", "|---|---|---|---|---|"]
    for name, r in per_repo.items():
        n_calls = sum(len(v) for v in r["calls"].values())
        used_any |= set(r["calls"])
        out.append(f"| {name} | {len(r['declared'])} | {len(r['imports'])} | {len(r['calls'])} | {n_calls} |")
    for name, r in per_repo.items():
        if not (r["declared"] or r["imports"]):
            continue
        out += ["", f"## {name}"]
        for d in r["declared"]:
            out.append(f"- declared `{d['file']}`: `{d['line']}`")
        for d in r["imports"][:15]:
            out.append(f"- import `{d['file']}`: `{d['line']}`")
        for sym, sites in r["calls"].items():
            out.append(f"- **{sym}** ×{len(sites)}: " + ", ".join(f"`{s}`" for s in sites[:8]) + (" …" if len(sites) > 8 else ""))
    unused = sorted(set(exported) - used_any)
    if exported:
        out += ["", "## Public symbols nobody outside the library calls",
                ", ".join(f"`{s}`" for s in unused[:40]) if unused else "None: every public symbol is used somewhere."]
    versions = {name: [d["line"] for d in r["declared"]] for name, r in per_repo.items() if r["declared"]}
    if len({tuple(v) for v in versions.values()}) > 1:
        out += ["", "## Version declarations differ between repos"] + [f"- {n}: " + "; ".join(f"`{x}`" for x in v)
                                                                      for n, v in versions.items()]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("library")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--max-sites", type=int, default=30)
    a = ap.parse_args(argv)
    target = Path(a.target).resolve()
    ctx = wslib.Context(target)
    root = ctx.repo if ctx.mode == "single" else target
    def_name, def_root, prefix, ids = resolve(root, ctx, a.library)
    exported = exports(def_root, ids, prefix)
    per_repo = {}
    for name, path, _m, _l in ctx.maps():
        if not path.is_dir():
            continue
        if ctx.mode == "workspace" and name == def_name:
            continue
        per_repo[name] = trace_repo(path, ids, exported, exclude=prefix, max_sites=a.max_sites)
    def_label = def_name or (prefix.rstrip("/") if prefix else (root.name if def_root else None))
    md = render(a.library, def_label, def_root, ids, exported, per_repo)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"wrote {a.out}")
    if a.json:
        Path(a.json).write_text(json.dumps({"library": a.library, "defined_in": def_label,
                                            "ids": {k: sorted(v) for k, v in ids.items()},
                                            "exports": exported, "repos": per_repo}, indent=2) + "\n")
    if not a.out:
        print(md)
    found = any(r["imports"] or r["declared"] for r in per_repo.values())
    if not found:
        print(f"note: no repo imports or declares {a.library}. Check the name (package, module or repo name).")
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
