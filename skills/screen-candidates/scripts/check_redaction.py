#!/usr/bin/env python3
"""Verify redacted CVs contain no identifying details before any scoring.

Usage: python3 check_redaction.py hiring/<role-slug> [--strict]

Fails any candidate whose name in identities.json is not confirmed. Then checks every
redacted/<id>.md for: emails, phone numbers, profile/code/web links, date of birth and age
statements, nationality/gender/marital/religion fields (EN, FR, DE, ES, IT, NL, PT labels),
photos, and any part of the candidate's confirmed name or aliases.
--strict also fails on gendered words, titles and family-status words.
CVs in other languages need the agent's manual review; patterns cannot vouch for them.

Exit code 0 = clean, 1 = leaks found (do not score until fixed).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hiring_lib as H  # noqa: E402


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    role = Path(argv[1])
    strict = "--strict" in argv
    mapping = H.load_json(role / "candidates.json")
    identities = H.load_identities(role)
    failures = 0
    for cid in sorted(mapping):
        red_path = role / "redacted" / f"{cid}.md"
        if not red_path.exists():
            print(f"FAIL {cid}: redacted file missing")
            failures += 1
            continue
        red = red_path.read_text(encoding="utf-8")
        ident = identities.get(cid, {})
        if not ident.get("confirmed") or not ident.get("name"):
            print(f"FAIL {cid}: name not confirmed (identities.py list / confirm / set)")
            failures += 1
            continue
        hits = H.find_pii(red, H.identity_names(ident))
        soft = H.find_soft(red)
        if strict:
            hits += soft
        if hits:
            failures += 1
            shown = "; ".join(f"{k}: {s!r}" for k, s in hits[:8])
            print(f"FAIL {cid}: {shown}{' ...' if len(hits) > 8 else ''}")
        elif soft:
            print(f"WARN {cid}: review words " + ", ".join(sorted({w.lower() for _, w in soft})))
        else:
            print(f"ok   {cid}")
    print(f"\n{len(mapping) - failures}/{len(mapping)} clean.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
