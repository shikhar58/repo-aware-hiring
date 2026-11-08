#!/usr/bin/env python3
"""Confirm or correct each candidate's name before scoring. Redaction depends on it.

Usage:
  identities.py list <role_dir>                       show ids, detected names and status
  identities.py set <role_dir> <id> "<full name>" [--alias "<other form>" ...]
                                                      set the name (marks it confirmed)
  identities.py confirm <role_dir> <id> [<id> ...]    confirm detected names as correct
  identities.py confirm <role_dir> --all              confirm every detected name (only after checking each)

After `set`, re-run prepare_cvs.py so the corrected name is redacted, then check_redaction.py.
identities.json holds personal data and is deleted when the round is closed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hiring_lib as H  # noqa: E402


def save(role, ids):
    H.write_json(Path(role) / "identities.json", dict(sorted(ids.items())))


def main(argv):
    if len(argv) < 3 or argv[1] not in {"list", "set", "confirm"}:
        print(__doc__)
        return 2
    cmd, role = argv[1], Path(argv[2])
    ids = H.load_identities(role)
    if not ids:
        print("No identities.json: run prepare_cvs.py first.")
        return 1

    if cmd == "list":
        names = H.load_json(role / "candidates.json")
        for cid in sorted(ids):
            e = ids[cid]
            alias = f" (aliases: {', '.join(e.get('aliases', []))})" if e.get("aliases") else ""
            status = "confirmed" if e.get("confirmed") else "UNCONFIRMED"
            print(f"{cid}  {status:<12} {e.get('name') or '— not detected —'}{alias}   [{names.get(cid, '?')}]")
        return 0

    if cmd == "set":
        if len(argv) < 5 or argv[3] not in ids:
            print("usage: identities.py set <role_dir> <id> \"<full name>\" [--alias \"...\"]")
            return 2
        cid, name = argv[3], argv[4].strip()
        aliases = [argv[i + 1] for i, a in enumerate(argv) if a == "--alias" and i + 1 < len(argv)]
        if len(H.name_tokens(name)) < 1:
            print("That does not look like a name.")
            return 1
        ids[cid] = {"name": name, "aliases": aliases, "source": "agent", "confirmed": True}
        save(role, ids)
        print(f"{cid}: set and confirmed. Re-run prepare_cvs.py to apply, then check_redaction.py.")
        return 0

    targets = sorted(ids) if "--all" in argv else argv[3:]
    missing = [t for t in targets if t not in ids]
    if missing or not targets:
        print(f"Unknown or no ids: {missing or '(none given)'}")
        return 2
    blocked = [t for t in targets if not ids[t].get("name")]
    for t in targets:
        if ids[t].get("name"):
            ids[t]["confirmed"] = True
    save(role, ids)
    print(f"Confirmed {len(targets) - len(blocked)}.")
    if blocked:
        print(f"No name detected for {', '.join(blocked)}: use `set` for those.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
