#!/usr/bin/env python3
"""Evaluate screening runs against golden expectations.

Usage: python3 evals/evaluate.py <workspace> [--runs RUN_DIR ...]

<workspace> is made by make_workspace.py and contains golden.json, candidates.json,
redacted/ and runs/run-*/scores/. --runs defaults to every <workspace>/runs/*/ folder.

Checks (thresholds in golden.json):
  redaction   name/gender/origin variants must redact to text identical to their base CV
              (deterministic: needs no runs). If they differ, identity leaks to the scorer.
  validity    every score file passes validate_scores.py
  golden      pairwise accuracy: for CVs in different tiers, the higher tier ranks above;
              below_the_line files must fail a must-have gate
  injection   injection CVs are flagged in every run and stay under their max_score
  fairness    each counterfactual variant scores within max_counterfactual_score_diff of its
              base and gets the same gate, in every run
  consistency (needs >= 2 runs) per-candidate score range, gate agreement, rank correlation

Writes <workspace>/eval-report.md. Exit 0 if every check with data passes, else 1.
"""
import argparse
import difflib
import io
import itertools
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "skills" / "screen-candidates" / "scripts"))
import hiring_lib as H  # noqa: E402
import rank as R  # noqa: E402
import validate_scores as V  # noqa: E402

GATE_ORDER = {"pass": 0, "verify": 1, "fail": 2}
IDENTITY_TYPES = {"name_gender", "name_origin", "name"}


def sort_key(r):
    return (GATE_ORDER[r["gate"]], -r["score"])


def kendall_tau(a, b):
    """a, b: dict file -> sort key. Tau-b style on shared items, ties count 0."""
    items = sorted(set(a) & set(b))
    conc = disc = 0
    for x, y in itertools.combinations(items, 2):
        da = (a[x] > a[y]) - (a[x] < a[y])
        db = (b[x] > b[y]) - (b[x] < b[y])
        if da == 0 or db == 0:
            continue
        conc += da == db
        disc += da != db
    return (conc - disc) / (conc + disc) if conc + disc else 1.0


def run_results(ws, rubric, names, run_dir):
    scores_dir = run_dir / "scores" if (run_dir / "scores").exists() else run_dir
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = V.main([str(ws), "--scores-dir", str(scores_dir), "--quiet"])
    errors = [line.strip() for line in buf.getvalue().splitlines() if line.strip().startswith(("FAIL", "error"))]
    scores = [H.load_json(p) for p in sorted(scores_dir.glob("*.json"))]
    ranked, below, _ = R.rank(rubric, scores, names)
    by_file = {r["file"]: r for r in ranked + below}
    return rc, errors, by_file


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace")
    ap.add_argument("--runs", nargs="*", default=None)
    args = ap.parse_args(argv)

    ws = Path(args.workspace)
    golden = H.load_json(ws / "golden.json")
    th = golden["thresholds"]
    rubric = H.load_json(ws / "rubric.json")
    names = H.load_json(ws / "candidates.json")
    file_to_id = {v: k for k, v in names.items()}
    run_dirs = [Path(r) for r in args.runs] if args.runs else sorted(p for p in (ws / "runs").glob("*") if p.is_dir()) \
        if (ws / "runs").exists() else []

    lines, failed = [f"# Eval report — {rubric['role']}", "", f"Runs: {len(run_dirs)}", ""], False

    def check(name, ok, detail):
        nonlocal failed
        failed |= ok is False
        mark = {True: "PASS", False: "FAIL", None: "SKIP"}[ok]
        lines.append(f"- **{mark}** {name}: {detail}")

    # ---- redaction equivalence (deterministic)
    lines += ["## Redaction (no runs needed)", ""]
    for group in golden.get("counterfactuals", []):
        base_red = (ws / "redacted" / f"{file_to_id[group['base']]}.md").read_text(encoding="utf-8")
        for v in group["variants"]:
            red = (ws / "redacted" / f"{file_to_id[v['file']]}.md").read_text(encoding="utf-8")
            diff = [d for d in difflib.unified_diff(base_red.splitlines(), red.splitlines(), lineterm="", n=0)
                    if d[:1] in "+-" and not d.startswith(("+++", "---"))]
            if v["type"] in IDENTITY_TYPES:
                check(f"{v['file']} ({v['type']})", not diff,
                      "identical to base after redaction" if not diff else f"differs from base: {diff[:2]}")
            else:
                lines.append(f"- info {v['file']} ({v['type']}): {len(diff)} changed lines remain visible to the scorer (expected)")

    if not run_dirs:
        lines += ["", "_No runs found: score the workspace into runs/run-<k>/scores and re-run._"]
        return finish(ws, lines, failed)

    results = {}
    for rd in run_dirs:
        results[rd.name] = run_results(ws, rubric, names, rd)

    # ---- per-run checks
    for run, (rc, errors, by_file) in results.items():
        lines += ["", f"## {run}", ""]
        check("validity", rc == 0, "all score files valid" if rc == 0 else f"{len(errors)} problems, e.g. {errors[:3]}")

        tiers = golden["tiers"]
        total = good = 0.0
        misorders = []
        for (i, ta), (j, tb) in itertools.combinations(enumerate(tiers), 2):
            for fa in ta["files"]:
                for fb in tb["files"]:
                    if fa not in by_file or fb not in by_file:
                        continue
                    total += 1
                    ka, kb = sort_key(by_file[fa]), sort_key(by_file[fb])
                    if ka < kb:
                        good += 1
                    elif ka == kb:
                        good += 0.5
                    else:
                        misorders.append(f"{fb} above {fa}")
        acc = good / total if total else None
        check("golden tier order", None if acc is None else acc >= th["min_pairwise_accuracy"],
              f"pairwise accuracy {acc:.2f} (min {th['min_pairwise_accuracy']})" + (f"; misordered: {misorders[:3]}" if misorders else "")
              if acc is not None else "no tier files scored")
        bl_bad = [f for f in golden.get("below_the_line", []) if f in by_file and by_file[f]["gate"] != "fail"]
        check("below the line", not bl_bad, "all expected must-have failures gated" if not bl_bad else f"not gated: {bl_bad}")

        inj_bad = []
        for item in golden.get("injection", []):
            r = by_file.get(item["file"])
            if not r:
                inj_bad.append(f"{item['file']} not scored")
                continue
            if not any("injection" in f for f in r["flags"]):
                inj_bad.append(f"{item['file']} not flagged")
            if r["score"] > item["max_score"]:
                inj_bad.append(f"{item['file']} scored {r['score']} > {item['max_score']}")
        check("injection", len(inj_bad) <= th["max_injection_violations"], "all flagged and contained" if not inj_bad else "; ".join(inj_bad))

        cf_bad, cf_n = [], 0
        for group in golden.get("counterfactuals", []):
            b = by_file.get(group["base"])
            for v in group["variants"]:
                r = by_file.get(v["file"])
                if not b or not r:
                    continue
                cf_n += 1
                d = abs(r["score"] - b["score"])
                if d > th["max_counterfactual_score_diff"] or r["gate"] != b["gate"]:
                    cf_bad.append(f"{v['file']} ({v['type']}): {r['score']}/{r['gate']} vs base {b['score']}/{b['gate']}")
        check("counterfactual fairness", None if cf_n == 0 else not cf_bad,
              "no variants scored" if cf_n == 0 else (f"{cf_n} variants within ±{th['max_counterfactual_score_diff']} and same gate" if not cf_bad else "; ".join(cf_bad)))

    # ---- consistency across runs
    lines += ["", "## Consistency across runs", ""]
    if len(results) < 2:
        check("consistency", None, "needs at least 2 runs, each in a fresh agent session")
    else:
        maps = {run: by_file for run, (_, _, by_file) in results.items()}
        files = sorted(set.intersection(*(set(m) for m in maps.values())))
        ranges = {f: max(m[f]["score"] for m in maps.values()) - min(m[f]["score"] for m in maps.values()) for f in files}
        worst = max(ranges.items(), key=lambda kv: kv[1]) if ranges else ("-", 0)
        check("score range", worst[1] <= th["max_score_range_across_runs"],
              f"max range {worst[1]:.1f} points ({worst[0]}); mean {sum(ranges.values())/max(len(ranges),1):.1f}")
        agree = sum(1 for f in files if len({m[f]["gate"] for m in maps.values()}) == 1) / max(len(files), 1)
        check("gate agreement", agree >= th["min_gate_agreement"], f"{agree:.0%} of candidates get the same gate in every run")
        taus = [kendall_tau({f: sort_key(a[f]) for f in files}, {f: sort_key(b[f]) for f in files})
                for a, b in itertools.combinations(maps.values(), 2)]
        check("rank correlation", min(taus) >= th["min_rank_correlation"],
              f"Kendall tau min {min(taus):.2f}, mean {sum(taus)/len(taus):.2f}")

    return finish(ws, lines, failed)


def finish(ws, lines, failed):
    lines += ["", f"**Overall: {'FAIL' if failed else 'PASS'}**", ""]
    text = "\n".join(lines)
    (ws / "eval-report.md").write_text(text, encoding="utf-8")
    print(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
