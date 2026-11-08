#!/usr/bin/env python3
"""Validate interview kits before they are used.

Usage: python3 validate_kit.py hiring/<role-slug> [--candidates C01 C02 ...]

core.json (asked of every candidate):
  - every must-have and important criterion has at least one core question
  - each question has follow-ups, listen_for, warning_signs and minutes; criterion ids exist
<id>.json (per candidate):
  - candidate id and rubric version match; 1-6 personal questions; known types and criteria
  - a gap_probe for every must-have whose status is no_evidence or weak (error); for important criteria with
    those statuses, a warning only if no core question covers them either
  - claim_deep_dive evidence is quoted verbatim from the candidate's redacted CV, and never injection text
  - core + personal minutes fit the interview length
Everything a candidate will hear (questions and follow-ups):
  - no internal details (same checks as job descriptions: paths, internal names, env vars, hosts, weaknesses)
  - no questions about protected characteristics (age, family, nationality, health, religion, ...)

Exit code 0 = valid (warnings allowed), 1 = errors.
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
sys.path.insert(0, str(SKILLS / "screen-candidates" / "scripts"))
sys.path.insert(0, str(SKILLS / "write-job-description" / "scripts"))
import check_jd  # noqa: E402
import hiring_lib as H  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel as P  # noqa: E402

TYPES = {"claim_deep_dive", "gap_probe", "consistency"}
REQUIRED = ("question", "follow_ups", "listen_for", "warning_signs", "minutes")

# Questions that must never be asked. Patterns avoid tech homonyms ("race condition", "UNION", "health check").
PROTECTED = [
    (r"\bhow old\b|\byour age\b|\bage are you\b|\bwhen were you born\b|\bdate of birth\b|\bgraduat\w* year\b|\bwhat year did you graduate\b", "age"),
    (r"\bmarried\b|\bspouse\b|\bhusband\b|\bwife\b|\bpartner'?s job\b|\bchildren\b(?! (?:nodes?|process|elements?))|\bkids\b|\bpregnan\w*|\bfamily (?:plans?|status|situation)\b|\bstart a family\b|\bchildcare\b", "family"),
    (r"\breligio\w*|\bchurch\b|\bmosque\b|\btemple\b|\bsynagogue\b|\bpray\w*\b|\bholy days?\b", "religion"),
    (r"\bnationality\b|\bwhere are you (?:originally |really )?from\b|\bwhere were you born\b|\bcitizenship\b|\bnative (?:language|tongue|country)\b|\bmother tongue\b|\baccent\b|\bethnic\w*", "national origin or ethnicity"),
    (r"\bhealth (?:condition|issues?|problems?)\b|\bdisabilit\w*|\bsick (?:leave|days)\b|\bmedical (?:condition|history)\b|\bmedication\b|\bmental health\b", "health or disability"),
    (r"\bgender\b|\bsexual\w*|\bboyfriend\b|\bgirlfriend\b", "gender or sexuality"),
    (r"\btrade union\b|\bunion member\w*\b|\bpolitic\w*\b|\bvote\b", "union membership or politics"),
    (r"\b(?:why|explain|what happened)\b[^.?\n]{0,40}\b(?:gap|career break|time off)\b|\bgap in your (?:cv|resume|employment)\b", "reasons for employment gaps"),
    (r"\barrest\w*|\bcriminal\b|\bconvict\w*", "criminal history (an HR matter, if lawful at all)"),
]
PROTECTED_RE = [(re.compile(p, re.I), what) for p, what in PROTECTED]


def check_question(q, valid_crit, where, errors, warnings):
    for f in REQUIRED:
        if f not in q or q[f] in (None, "", []):
            errors.append(f"{where}: missing {f}")
    if q.get("criterion") not in valid_crit:
        errors.append(f"{where}: unknown criterion {q.get('criterion')!r}")
    if not isinstance(q.get("minutes", 0), (int, float)) or not 1 <= q.get("minutes", 0) <= 30:
        errors.append(f"{where}: minutes must be between 1 and 30")
    for k in ("follow_ups", "listen_for", "warning_signs"):
        if k in q and not isinstance(q[k], list):
            errors.append(f"{where}: {k} must be a list")


def candidate_facing(q):
    return "\n".join([q.get("question", "")] + [str(x) for x in q.get("follow_ups", [])])


def check_text(text, role, where, errors):
    for line_no, msg in check_jd.find_leaks(text, role):
        errors.append(f"{where}: candidate will hear an internal detail: {msg}")
    for rx, what in PROTECTED_RE:
        m = rx.search(text)
        if m:
            errors.append(f"{where}: asks about a protected characteristic ({what}): {m.group(0)!r}")
    if H.scan_injection(text):
        errors.append(f"{where}: contains injection-like text")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role_dir")
    ap.add_argument("--candidates", nargs="*", default=None, help="default: every <id>.json in interviews/")
    args = ap.parse_args(argv)
    role = Path(args.role_dir)
    kdir = role / "interviews"
    rubric = H.load_json(role / "rubric.json")
    crit = {c["id"]: c for c in rubric["criteria"]}
    errors, warnings = [], []

    core_path = kdir / "core.json"
    if not core_path.exists():
        print(f"ERROR: {core_path} missing: write the core questions first.")
        return 1
    core = H.load_json(core_path)
    if core.get("rubric_version") != rubric.get("version"):
        errors.append(f"core.json: rubric_version {core.get('rubric_version')} != {rubric.get('version')}")
    duration = core.get("duration_minutes")
    if not isinstance(duration, (int, float)) or duration < 15:
        errors.append("core.json: duration_minutes missing or under 15")
        duration = 60
    covered = set()
    ids = set()
    for i, q in enumerate(core.get("questions", []), 1):
        where = f"core.json #{i} ({q.get('id', '?')})"
        if q.get("id") in ids:
            errors.append(f"{where}: duplicate id")
        ids.add(q.get("id"))
        check_question(q, crit, where, errors, warnings)
        check_text(candidate_facing(q), role, where, errors)
        covered.add(q.get("criterion"))
    for cid, c in crit.items():
        if c["tier"] in ("must_have", "important") and cid not in covered:
            (errors if c["tier"] == "must_have" else warnings).append(
                f"core.json: no core question for {c['tier'].replace('_', '-')} criterion {c['name']!r}")
    core_minutes = sum(q.get("minutes", 0) for q in core.get("questions", []) if isinstance(q.get("minutes"), (int, float)))
    if core_minutes > duration:
        errors.append(f"core.json: core questions take {core_minutes} min, interview is {duration}")

    files = [kdir / f"{c}.json" for c in args.candidates] if args.candidates else \
        sorted(p for p in kdir.glob("*.json") if p.stem != "core")
    if not files:
        warnings.append("no candidate kits yet")
    prep = H.load_json(role / "prep_report.json") if (role / "prep_report.json").exists() else {}
    kits_loaded = []
    for path in files:
        cid = path.stem
        if not path.exists():
            errors.append(f"{cid}: kit missing")
            continue
        kit = H.load_json(path)
        if kit.get("candidate_id") != cid:
            errors.append(f"{cid}: candidate_id {kit.get('candidate_id')!r} does not match file name")
        if kit.get("rubric_version") != rubric.get("version"):
            errors.append(f"{cid}: rubric_version mismatch")
        qs = kit.get("questions", [])
        if not 1 <= len(qs) <= 6:
            errors.append(f"{cid}: {len(qs)} personal questions (expected 1-6)")
        score_path = role / "scores" / f"{cid}.json"
        score = H.load_json(score_path) if score_path.exists() else {}
        red_path = role / "redacted" / f"{cid}.md"
        redacted = red_path.read_text(encoding="utf-8") if red_path.exists() else None
        if not score:
            warnings.append(f"{cid}: no score file, so gap coverage can't be checked")
        probed = set()
        core_texts = {q.get("question", "").strip().lower() for q in core.get("questions", [])}
        for i, q in enumerate(qs, 1):
            where = f"{cid} #{i} ({q.get('id', '?')})"
            check_question(q, crit, where, errors, warnings)
            check_text(candidate_facing(q), role, where, errors)
            if q.get("type") not in TYPES:
                errors.append(f"{where}: type must be one of {sorted(TYPES)}")
            if not q.get("why"):
                errors.append(f"{where}: missing why (what it tests, for the interviewer)")
            if q.get("question", "").strip().lower() in core_texts:
                errors.append(f"{where}: repeats a core question")
            if q.get("type") == "gap_probe":
                probed.add(q.get("criterion"))
            if q.get("type") == "claim_deep_dive":
                ev = q.get("evidence") or []
                if not ev:
                    errors.append(f"{where}: claim_deep_dive needs the quoted claim in evidence")
                for item in ev:
                    if H.scan_injection(item):
                        errors.append(f"{where}: evidence quotes injection text")
                    elif redacted is not None and H.grounding(item, redacted) < 0.8:
                        errors.append(f"{where}: evidence not found in the candidate's CV: {item[:70]!r}")
        for c_id, entry in score.get("criteria", {}).items():
            c = crit.get(c_id)
            if not c or entry.get("status") not in ("no_evidence", "weak"):
                continue
            if c_id in probed:
                continue
            if c["tier"] == "must_have":
                errors.append(f"{cid}: must-have {c['name']!r} is {entry['status'].replace('_', ' ')} on the CV but has no gap_probe")
            elif c["tier"] == "important" and c_id not in covered:
                warnings.append(f"{cid}: important criterion {c['name']!r} is {entry['status'].replace('_', ' ')}; consider a gap_probe")
        total = core_minutes + sum(q.get("minutes", 0) for q in qs if isinstance(q.get("minutes"), (int, float)))
        if total > duration:
            errors.append(f"{cid}: core + personal questions take {total} min, interview is {duration}")
        if prep.get(cid, {}).get("injection") and not any("injection" in str(n).lower() for n in kit.get("notes_for_interviewer", [])):
            warnings.append(f"{cid}: CV was flagged for possible prompt injection; mention it in notes_for_interviewer")
        kits_loaded.append((cid, kit))

    pe, pw = P.validate(core, set(crit), kits_loaded)
    errors += pe
    warnings += pw

    for e in errors:
        print(f"ERROR {e}")
    for w in warnings:
        print(f"warn  {w}")
    print(f"\n{len(files)} candidate kits, {len(errors)} errors, {len(warnings)} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
