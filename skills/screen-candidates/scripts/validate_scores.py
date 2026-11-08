#!/usr/bin/env python3
"""Validate score files before ranking.

Usage: python3 validate_scores.py hiring/<role-slug> [--scores-dir DIR] [--min-grounding 0.8]

For each scores/<id>.json checks:
  - schema: candidate_id matches file, rubric_version matches, every rubric criterion present,
    no unknown criteria, level 0-3, status/confidence from the allowed sets
  - consistency: level 0 <-> status no_evidence|contradicted; weak -> level 1;
    evidenced -> level >= 1
  - evidence: required unless status is no_evidence; each item must be grounded in the
    candidate's redacted CV (token overlap >= --min-grounding), which catches invented evidence
  - injection: if prepare_cvs.py found injection text in the CV, the score must carry the
    possible_prompt_injection flag
  - completeness: strengths, gaps and interview_probes are non-empty lists

Exit code 0 = valid, 1 = errors (fix and re-run before rank.py).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hiring_lib as H  # noqa: E402


def validate_one(path, rubric, redacted_text, injection_hits, min_grounding):
    errors, warnings = [], []
    try:
        s = H.load_json(path)
    except Exception as e:  # noqa: BLE001
        return [f"invalid JSON: {e}"], []
    cid = path.stem
    if s.get("candidate_id") != cid:
        errors.append(f"candidate_id {s.get('candidate_id')!r} does not match file name")
    if s.get("rubric_version") != rubric.get("version"):
        errors.append(f"rubric_version {s.get('rubric_version')} != current {rubric.get('version')}")

    ids = [c["id"] for c in rubric["criteria"]]
    crit = s.get("criteria")
    if not isinstance(crit, dict):
        return errors + ["criteria missing or not an object"], warnings
    for missing in [i for i in ids if i not in crit]:
        errors.append(f"missing criterion {missing}")
    for extra in [k for k in crit if k not in ids]:
        errors.append(f"unknown criterion {extra}")

    for k, e in crit.items():
        if k not in ids:
            continue
        lvl, st, conf = e.get("level"), e.get("status"), e.get("confidence")
        ev = e.get("evidence", [])
        if lvl not in H.LEVELS:
            errors.append(f"{k}: level {lvl!r} not in 0-3")
        if st not in H.STATUSES:
            errors.append(f"{k}: status {st!r} not in {sorted(H.STATUSES)}")
        if conf not in H.CONFIDENCES:
            errors.append(f"{k}: confidence {conf!r} not in {sorted(H.CONFIDENCES)}")
        if lvl == 0 and st not in {"no_evidence", "contradicted"}:
            errors.append(f"{k}: level 0 requires status no_evidence or contradicted")
        if lvl in {1, 2, 3} and st not in {"evidenced", "weak"}:
            errors.append(f"{k}: level {lvl} requires status evidenced or weak")
        if st == "weak" and lvl != 1:
            errors.append(f"{k}: status weak requires level 1")
        if not isinstance(ev, list):
            errors.append(f"{k}: evidence must be a list")
            continue
        if st != "no_evidence" and not ev:
            errors.append(f"{k}: status {st} needs at least one evidence quote")
        if st == "no_evidence" and ev:
            warnings.append(f"{k}: no_evidence but evidence listed")
        for item in ev:
            if H.scan_injection(item):
                errors.append(f"{k}: evidence quotes injection text, which can never support a score: {item[:70]!r}")
        if redacted_text is not None:
            for item in ev:
                g = H.grounding(item, redacted_text)
                if g < min_grounding:
                    errors.append(f"{k}: evidence not found in CV (grounding {g:.2f}): {item[:70]!r}")

    for field in ("strengths", "gaps", "interview_probes"):
        v = s.get(field)
        if not isinstance(v, list) or not v:
            errors.append(f"{field} must be a non-empty list")
    flags = s.get("flags", [])
    if not isinstance(flags, list):
        errors.append("flags must be a list")
        flags = []
    if injection_hits and not any("injection" in str(f) for f in flags):
        errors.append(f"CV contains suspected injection text {injection_hits[0]!r} but no possible_prompt_injection flag")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role_dir")
    ap.add_argument("--scores-dir", default=None, help="default: <role_dir>/scores")
    ap.add_argument("--min-grounding", type=float, default=0.8)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    role = Path(args.role_dir)
    rubric = H.load_json(role / "rubric.json")
    scores_dir = Path(args.scores_dir) if args.scores_dir else role / "scores"
    prep = H.load_json(role / "prep_report.json") if (role / "prep_report.json").exists() else {}
    mapping = H.load_json(role / "candidates.json") if (role / "candidates.json").exists() else {}

    files = sorted(scores_dir.glob("*.json"))
    unscored = sorted(set(mapping) - {p.stem for p in files})
    total_err = 0
    for p in files:
        red_path = role / "redacted" / f"{p.stem}.md"
        red = red_path.read_text(encoding="utf-8") if red_path.exists() else None
        errs, warns = validate_one(p, rubric, red, prep.get(p.stem, {}).get("injection", []), args.min_grounding)
        if red is None:
            warns.append("no redacted CV found; evidence grounding skipped")
        total_err += len(errs)
        if not args.quiet or errs:
            status = "FAIL" if errs else ("warn" if warns else "ok  ")
            print(f"{status} {p.stem}")
            for e in errs:
                print(f"     error: {e}")
            for w in warns:
                print(f"     warn:  {w}")
    if unscored:
        print(f"\nNot yet scored: {', '.join(unscored)}")
    print(f"\n{len(files)} score files, {total_err} errors.")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
