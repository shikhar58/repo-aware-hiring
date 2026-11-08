#!/usr/bin/env python3
"""Deterministic ranking for repo-aware-hiring.

Usage: python3 rank.py hiring/<role-slug> [--scores-dir DIR] [--out FILE] [--json] [--skip-validate]

Validates score files first (validate_scores.py) and refuses to rank if any are invalid.
Then computes weighted totals, applies must-have gates and writes ranking.json.

Score = sum(level / 3 * weight) over important and nice_to_have criteria, normalised to 100.

Must-have gates:
  level >= 1                 -> pass
  level 0, no_evidence       -> verify  (ranked, but after every 'pass' candidate)
  level 0, contradicted      -> fail    (listed below the line, unranked)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hiring_lib as H  # noqa: E402
import validate_scores  # noqa: E402

MAX_LEVEL = 3
GATE_ORDER = {"pass": 0, "verify": 1}


def rank(rubric, scores, names):
    criteria = rubric["criteria"]
    must = [c for c in criteria if c["tier"] == "must_have"]
    weighted = [c for c in criteria if c["tier"] != "must_have"]
    total_weight = sum(c.get("weight", 0) for c in weighted)

    results = []
    for s in scores:
        cid = s["candidate_id"]
        crit = s.get("criteria", {})
        gate, notes = "pass", []
        for c in must:
            e = crit.get(c["id"], {"level": 0, "status": "no_evidence"})
            if e.get("level", 0) >= 1:
                continue
            if e.get("status") == "contradicted":
                gate = "fail"
                notes.append(f"fails: {c['name']}")
            else:
                gate = "verify" if gate == "pass" else gate
                notes.append(f"verify: {c['name']}")
        raw = sum(max(0, min(MAX_LEVEL, crit.get(c["id"], {}).get("level", 0))) / MAX_LEVEL * c.get("weight", 0)
                  for c in weighted)
        score = round(raw * 100 / total_weight, 1) if total_weight else 0.0
        confs = [e.get("confidence", "medium") for e in crit.values()]
        if confs and confs.count("low") * 3 >= len(confs):
            confidence = "low"
        elif confs and all(x == "high" for x in confs):
            confidence = "high"
        else:
            confidence = "medium"
        results.append({"candidate_id": cid, "file": names.get(cid, ""), "score": score, "gate": gate,
                        "gate_notes": notes, "confidence": confidence, "flags": s.get("flags", [])})

    ranked = sorted([r for r in results if r["gate"] != "fail"],
                    key=lambda r: (GATE_ORDER[r["gate"]], -r["score"], r["candidate_id"]))
    # Equal score within the same gate group = tie: same rank number, marked so no one
    # reads meaning into an order that only reflects file names.
    prev = None
    for i, r in enumerate(ranked, 1):
        key = (r["gate"], r["score"])
        if prev and key == prev[0]:
            r["rank"] = prev[1]["rank"]
            r["tied"] = prev[1]["tied"] = True
        else:
            r["rank"] = i
            r.setdefault("tied", False)
        prev = (key, r)
    below = sorted([r for r in results if r["gate"] == "fail"], key=lambda r: r["candidate_id"])
    return ranked, below, total_weight


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role_dir")
    ap.add_argument("--scores-dir", default=None)
    ap.add_argument("--out", default=None, help="default: <role_dir>/ranking.json")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-validate", action="store_true", help="for debugging only")
    args = ap.parse_args(argv)

    role = Path(args.role_dir)
    rubric = H.load_json(role / "rubric.json")
    if not rubric.get("approved"):
        print("ERROR: rubric.json is not approved. Approve it before ranking.", file=sys.stderr)
        return 1
    scope = rubric.get("scope")
    if scope is not None:
        if not isinstance(scope, dict) or not scope or \
                not all(isinstance(v, (int, float)) and v >= 0 for v in scope.values()) or \
                abs(sum(scope.values()) - 1) > 0.01:
            print("ERROR: rubric.json scope must map each repo to a share of the work, summing to 1 "
                  "(e.g. {\"payments-lib\": 0.5, \"checkout-svc\": 0.3, \"billing-svc\": 0.2}).", file=sys.stderr)
            return 1
        unknown = [c["id"] for c in rubric["criteria"] for r in c.get("repos", []) or [] if r not in scope]
        if unknown:
            print(f"ERROR: criteria {sorted(set(unknown))} name repos that are not in rubric.json scope.", file=sys.stderr)
            return 1
    scores_dir = Path(args.scores_dir) if args.scores_dir else role / "scores"

    if not args.skip_validate:
        vargs = [str(role), "--scores-dir", str(scores_dir), "--quiet"]
        if validate_scores.main(vargs) != 0:
            print("ERROR: fix the score files above before ranking.", file=sys.stderr)
            return 1

    names = H.load_json(role / "candidates.json") if (role / "candidates.json").exists() else {}
    scores = [H.load_json(p) for p in sorted(scores_dir.glob("*.json"))]
    ranked, below, total_weight = rank(rubric, scores, names)
    if total_weight and abs(total_weight - 100) > 0.01:
        print(f"WARNING: weights sum to {total_weight}; scores normalised to 100.", file=sys.stderr)

    out = {"role": rubric.get("role"), "rubric_version": rubric.get("version"),
           "ranked": ranked, "below_the_line": below}
    out_path = Path(args.out) if args.out else role / "ranking.json"
    H.write_json(out_path, out)

    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    print(f"\n{out['role']} — rubric v{out['rubric_version']} — {len(scores)} candidates\n")
    print(f"{'Rank':<5}{'ID':<6}{'Score':>7}  {'Gate':<7}{'Conf':<7}File / notes")
    for r in ranked:
        notes = "; ".join(r["gate_notes"] + [f"FLAG {f}" for f in r["flags"]])
        rank_label = f"={r['rank']}" if r["tied"] else str(r["rank"])
        print(f"{rank_label:<5}{r['candidate_id']:<6}{r['score']:>7}  {r['gate']:<7}{r['confidence']:<7}{r['file']} {notes}")
    if below:
        print("\nBelow the line (contradicts a must-have):")
        for r in below:
            print(f"  {r['candidate_id']} {r['file']} — {'; '.join(r['gate_notes'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
