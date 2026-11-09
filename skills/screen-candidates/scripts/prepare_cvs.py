#!/usr/bin/env python3
"""Step 1 of screening: inventory, extract, first-pass redact, scan for injection.

Usage: python3 prepare_cvs.py hiring/<role-slug> [--force]

Writes (inside the role folder):
  candidates.json        id -> original filename (stable: existing ids are kept)
  identities.json        id -> candidate name, AUTO-DETECTED and UNCONFIRMED. The agent must check each
                         name against extracted/<id>.txt and confirm or correct it (identities.py);
                         check_redaction.py fails until every identity is confirmed.
  extracted/<id>.txt     raw text (contains personal data; deleted when the round closes)
  redacted/<id>.md       deterministic first-pass redaction (the agent reviews it)
  prep_report.json       per candidate: extraction problems, injection hits, review words, code links

Safe to re-run, e.g. after correcting names in identities.json: redacted files are regenerated
only if nobody edited them since the last run (use --force to overwrite manual edits).
Deterministic; does not call a model.
"""
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hiring_lib as H  # noqa: E402

MIN_CHARS = 200
PLACEHOLDER = re.compile(r"\[(?:NAME|EMAIL|PHONE|SOCIAL_LINK|CODE_LINK|WEB_LINK|DATE_OF_BIRTH|AGE|PERSONAL_FIELD|PHOTO)\]")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact(text, names):
    """Order matters: structured PII first (so an email containing the name is caught whole),
    then lines that consist of the name, then any remaining name tokens."""
    out_lines = []
    for line in text.splitlines():
        for kind, pat in H.PII_PATTERNS.items():
            def repl(m, kind=kind, line=line):
                s = m.group(0)
                if kind == "phone" and not H.phone_like(s, line):
                    return s
                return f"[{kind.upper()}]"
            line = pat.sub(repl, line)
        out_lines.append(line)

    name_set = {n.lower() for n in names}
    out_lines = [ln for ln in out_lines if H._clean_line(ln).lower() not in name_set]  # name heading lines
    out = "\n".join(out_lines)
    tokens = sorted({t for n in names for t in H.name_tokens(n)}, key=len, reverse=True)
    for tok in tokens:
        out = re.sub(rf"(?<!\w){re.escape(tok)}(?!\w)", "[NAME]", out, flags=re.I)
    kept = [ln for ln in out.splitlines()
            if not (PLACEHOLDER.search(ln) and re.sub(r"[#|·•,;:\-\s*]", "", PLACEHOLDER.sub("", ln)) == "")]
    return "\n".join(kept).strip() + "\n"


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    force = "--force" in argv
    if not args:
        print(__doc__)
        return 2
    role = Path(args[0])
    files = H.cv_files(role)
    if not files:
        print(f"No CVs found in {role / 'cvs'}", file=sys.stderr)
        return 1

    cand_path = role / "candidates.json"
    mapping = H.load_json(cand_path) if cand_path.exists() else {}
    by_file = {v: k for k, v in mapping.items()}
    next_n = max([int(k[1:]) for k in mapping] + [0]) + 1
    for f in files:
        if f.name not in by_file:
            cid = f"C{next_n:02d}"
            mapping[cid] = f.name
            by_file[f.name] = cid
            next_n += 1
    H.write_json(cand_path, dict(sorted(mapping.items())))

    round_path = role / "round.json"  # retention tracking for close-round
    if not round_path.exists():
        H.write_json(round_path, {"opened_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                                  "closed_at": None})

    identities = H.load_identities(role)
    old_report = H.load_json(role / "prep_report.json") if (role / "prep_report.json").exists() else {}
    if role.resolve().parent.name == "hiring" and not (role.resolve().parent / ".gitignore").exists():
        (role.resolve().parent / ".gitignore").write_text(
            "# Created by repo-aware-hiring. This folder holds candidate data and internal maps:\n"
            "# never commit it. Delete this file only if you really mean to version something here.\n*\n",
            encoding="utf-8")
    (role / "extracted").mkdir(exist_ok=True)
    (role / "redacted").mkdir(exist_ok=True)
    report = {}
    for f in files:
        cid = by_file[f.name]
        entry = {"file": f.name, "problems": [], "injection": [], "soft_words": [], "code_links": []}
        try:
            text = H.extract_text(f)
        except Exception as e:  # noqa: BLE001
            entry["problems"].append(f"unreadable: {e}")
            report[cid] = entry
            continue
        if len(text.strip()) < MIN_CHARS:
            entry["problems"].append("very little text extracted (scanned PDF or image?): needs OCR or manual review")
        (role / "extracted" / f"{cid}.txt").write_text(text, encoding="utf-8")

        ident = identities.get(cid)
        if ident is None:
            guess = H.probable_name(text)
            ident = {"name": guess, "aliases": [], "source": "auto", "confirmed": False}
            identities[cid] = ident
        if not ident.get("name"):
            entry["problems"].append("name not detected: set it with identities.py before scoring")

        red_path = role / "redacted" / f"{cid}.md"
        last_sha = old_report.get(cid, {}).get("redacted_sha256")
        edited = red_path.exists() and last_sha and sha(red_path.read_text(encoding="utf-8")) != last_sha
        if edited and not force:
            red = red_path.read_text(encoding="utf-8")
            entry["problems"].append("redacted file was edited by hand: kept (use --force to regenerate)")
        else:
            red = redact(text, H.identity_names(ident))
            red_path.write_text(red, encoding="utf-8")
        entry["redacted_sha256"] = sha(red)
        entry["code_links"] = sorted(set(m.group(0) for m in H.PII_PATTERNS["code_link"].finditer(text)))
        entry["injection"] = H.scan_injection(text)
        entry["soft_words"] = sorted({w.lower() for _, w in H.find_soft(red)})
        report[cid] = entry

    H.write_json(role / "identities.json", dict(sorted(identities.items())))
    H.write_json(role / "prep_report.json", report)
    n_inj = sum(1 for e in report.values() if e["injection"])
    n_prob = sum(1 for e in report.values() if e["problems"])
    unconfirmed = sum(1 for cid in report if not identities.get(cid, {}).get("confirmed"))
    print(f"Prepared {len(report)} CVs -> {role}. Injection suspects: {n_inj}. Problems: {n_prob}. "
          f"Names to confirm: {unconfirmed}.")
    for cid, e in report.items():
        notes = e["problems"] + [f"INJECTION: {s}" for s in e["injection"]]
        if e["soft_words"]:
            notes.append("review words: " + ", ".join(e["soft_words"]))
        if notes:
            print(f"  {cid} {e['file']}: " + " | ".join(notes))
    if unconfirmed:
        print("Next: check each name against extracted/<id>.txt and run identities.py confirm (or set).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
