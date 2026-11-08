#!/usr/bin/env python3
"""The decisions log: every planning checkpoint writes its answers here, so nothing is asked twice.

Usage:
  decisions.py add     <dir> --stage STAGE --key KEY --value VALUE [--assumed] [--note TEXT] [--by NAME]
  decisions.py get     <dir> KEY [--stage STAGE]        print the value (exit 1 if not decided)
  decisions.py list    <dir> [--stage STAGE] [--md]
  decisions.py pending <dir>                              assumptions nobody has confirmed yet
  decisions.py confirm <dir> KEY [--stage STAGE] [--value VALUE] [--by NAME]

<dir> is a role folder (hiring/<role>/ or roles/<role>/) for role decisions, or the workspace folder
(hiring/_repo/ in single-repo mode) for decisions shared by every role: repo tiers, ownership, mapping depth.
VALUE may be JSON (a list, an object, a number) or plain text.
"assumed" marks a default chosen without the hiring manager (they were away, or the session ran unattended):
artifacts built on it say so, and `pending` lists them for confirmation.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wslib  # noqa: E402

STAGES = ("workspace", "map", "system", "plan", "profile", "jd", "rubric", "screen", "interview", "close")


def path_for(d):
    d = Path(d)
    return d / "decisions.json" if d.suffix != ".json" else d


def load(d):
    p = path_for(d)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save(d, items):
    p = path_for(d)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_value(v):
    try:
        return json.loads(v)
    except ValueError:
        return v


def find(items, key, stage=None):
    hits = [x for x in items if x["key"] == key and (stage is None or x["stage"] == stage)]
    return hits[-1] if hits else None


def fmt(v):
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("dir"); p.add_argument("--stage", required=True, choices=STAGES)
    p.add_argument("--key", required=True); p.add_argument("--value", required=True)
    p.add_argument("--assumed", action="store_true"); p.add_argument("--note"); p.add_argument("--by")
    p = sub.add_parser("get"); p.add_argument("dir"); p.add_argument("key"); p.add_argument("--stage")
    p = sub.add_parser("list"); p.add_argument("dir"); p.add_argument("--stage"); p.add_argument("--md", action="store_true")
    p = sub.add_parser("pending"); p.add_argument("dir")
    p = sub.add_parser("confirm"); p.add_argument("dir"); p.add_argument("key"); p.add_argument("--stage")
    p.add_argument("--value"); p.add_argument("--by")
    a = ap.parse_args(argv)
    items = load(a.dir)

    if a.cmd == "add":
        prev = find(items, a.key, a.stage)
        entry = {"stage": a.stage, "key": a.key, "value": parse_value(a.value),
                 "status": "assumed" if a.assumed else "confirmed", "at": wslib.now()}
        if a.note:
            entry["note"] = a.note
        if a.by:
            entry["by"] = a.by
        if prev:
            entry["replaces"] = {"value": prev["value"], "status": prev["status"], "at": prev["at"]}
            items.remove(prev)
        items.append(entry)
        save(a.dir, items)
        print(f"{entry['status']}: [{a.stage}] {a.key} = {fmt(entry['value'])}" + (" (replaced earlier answer)" if prev else ""))
        return 0
    if a.cmd == "get":
        hit = find(items, a.key, a.stage)
        if not hit:
            return 1
        print(fmt(hit["value"]))
        return 0
    if a.cmd == "confirm":
        hit = find(items, a.key, a.stage)
        if not hit:
            print(f"no decision {a.key}")
            return 1
        if a.value is not None:
            hit["replaces"] = {"value": hit["value"], "status": hit["status"], "at": hit["at"]}
            hit["value"] = parse_value(a.value)
        hit["status"], hit["at"] = "confirmed", wslib.now()
        if a.by:
            hit["by"] = a.by
        save(a.dir, items)
        print(f"confirmed: [{hit['stage']}] {a.key} = {fmt(hit['value'])}")
        return 0
    rows = [x for x in items if (a.cmd != "pending" or x["status"] == "assumed")
            and (getattr(a, "stage", None) in (None, x["stage"]))]
    if getattr(a, "md", False):
        print("| Stage | Decision | Value | Status | When |\n|---|---|---|---|---|")
        for x in rows:
            print(f"| {x['stage']} | {x['key']} | {fmt(x['value'])[:80]} | {x['status']} | {x['at'][:10]} |")
    else:
        for x in rows:
            print(f"{x['status']:<9} [{x['stage']}] {x['key']} = {fmt(x['value'])[:100]}"
                  + (f"  ({x['note']})" if x.get("note") else ""))
    if a.cmd == "pending":
        print(f"{len(rows)} assumption(s) waiting for confirmation." if rows else "No pending assumptions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
