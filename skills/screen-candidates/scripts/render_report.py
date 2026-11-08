#!/usr/bin/env python3
"""Render report.md from ranking.json and the score files. Deterministic: no model involved.

Usage: python3 render_report.py hiring/<role-slug> [--notes FILE]

--notes: optional Markdown file (written by the agent) inserted under
"Rubric gaps worth noticing", e.g. where the JD and the repo disagree.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hiring_lib as H  # noqa: E402

DISCLAIMER = """> **Decision support only.** This report ranks CV evidence against an approved rubric.
> It does not reject or advance anyone. A named human reviewer must read each candidate's
> evidence before any decision. "No evidence" means the CV does not show it, not that the
> candidate lacks it: use the interview probes."""

METHOD = """## Method

- CVs were extracted and redacted (name, contact details, links, age, nationality) by
  `prepare_cvs.py`, reviewed, and verified clean by `check_redaction.py` before scoring.
- Each CV was scored alone against the rubric; candidates were not compared while scoring.
- `validate_scores.py` checked every score: allowed values, consistency, and that each
  evidence quote appears in the candidate's redacted CV.
- `rank.py` computed totals and order. Score = Σ (level / 3 × weight) over weighted
  criteria, out of 100. Must-haves are gates: level ≥ 1 passes; *no evidence* → "verify"
  (ranked after all passing candidates); *contradicted* → below the line.
- Equal scores are shown as ties (=N)."""


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("role_dir")
    ap.add_argument("--notes", default=None)
    args = ap.parse_args(argv)
    role = Path(args.role_dir)

    rubric = H.load_json(role / "rubric.json")
    ranking = H.load_json(role / "ranking.json")
    crit_by_id = {c["id"]: c for c in rubric["criteria"]}
    scores = {p.stem: H.load_json(p) for p in (role / "scores").glob("*.json")}
    rows = ranking["ranked"] + ranking["below_the_line"]

    out = [f"# Screening report — {rubric['role']}", "",
           f"Rubric v{rubric['version']} · approved by {rubric.get('approved_by') or '—'} · "
           f"{dt.date.today().isoformat()} · {len(rows)} candidates", "", DISCLAIMER, "",
           "## Shortlist", "",
           "| Rank | Candidate | File | Score /100 | Must-haves | Confidence | Flags |",
           "|---|---|---|---|---|---|---|"]
    for r in ranking["ranked"]:
        rank = f"={r['rank']}" if r.get("tied") else str(r["rank"])
        musts = "pass" if r["gate"] == "pass" else "verify: " + ", ".join(n.split(": ", 1)[1] for n in r["gate_notes"])
        flags = "⚠ injection" if any("injection" in f for f in r["flags"]) else ("⚠" if r["flags"] else "")
        out.append(f"| {rank} | {r['candidate_id']} | {esc(r['file'])} | {r['score']} | {esc(musts)} | {r['confidence']} | {flags} |")
    if ranking["below_the_line"]:
        out += ["", "**Below the line** (CV contradicts a must-have; unranked):", ""]
        for r in ranking["below_the_line"]:
            out.append(f"- {r['candidate_id']} — {esc(r['file'])} — {esc('; '.join(r['gate_notes']))}")

    out += ["", "## Rubric gaps worth noticing", ""]
    if args.notes and Path(args.notes).exists():
        out.append(Path(args.notes).read_text(encoding="utf-8").strip())
    else:
        out.append("_None recorded._")

    out += ["", "## Candidate detail"]
    for r in rows:
        s = scores.get(r["candidate_id"], {})
        title = f"{r['candidate_id']} — {r['file']} — {r['score']}/100"
        if r["gate"] == "fail":
            title += " — below the line"
        out += ["", f"### {title}", "", "**Strengths**"]
        out += [f"- {x}" for x in s.get("strengths", [])] or ["- —"]
        out += ["", "**Gaps / no evidence**"]
        out += [f"- {x}" for x in s.get("gaps", [])] or ["- —"]
        out += ["", "| Criterion | Tier | Level | Status | Evidence |", "|---|---|---|---|---|"]
        for cid_, c in crit_by_id.items():
            e = s.get("criteria", {}).get(cid_, {})
            ev = "; ".join(f"“{x}”" for x in e.get("evidence", [])) or "—"
            out.append(f"| {esc(c['name'])} | {c['tier'].replace('_', '-')} | {e.get('level', '—')}/3 | "
                       f"{e.get('status', '—').replace('_', ' ')} | {esc(ev)} |")
        out += ["", "**Interview probes (grounded in our repo)**"]
        out += [f"{i}. {p}" for i, p in enumerate(s.get("interview_probes", []), 1)]
        out += ["", "**Flags:** " + ("; ".join(s.get("flags", [])) or "none"), "", "---"]

    out += ["", METHOD, ""]
    (role / "report.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {role / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
