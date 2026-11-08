#!/usr/bin/env python3
"""Render interview kits as printable HTML scorecards and Markdown.

Usage: python3 render_kit.py hiring/<role-slug> [--candidates C01 C02 ...]

Writes interviews/<id>.html and interviews/<id>.md for each candidate kit, plus interviews/index.html.
The HTML is self-contained (no network requests) and escapes all text, like report.html.
Run validate_kit.py first.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "screen-candidates" / "scripts"))
import hiring_lib as H  # noqa: E402
import report_html as R  # noqa: E402

e = R.e
TYPE_LABEL = {"claim_deep_dive": "Deep dive into a CV claim", "gap_probe": "Probe a gap", "consistency": "Clarify"}

KIT_CSS = """
.agenda{display:flex;height:14px;border-radius:99px;overflow:hidden;margin:10px 0 6px;background:var(--panel2)}
.agenda span{display:block;height:100%}.agenda .core{background:var(--blue)}.agenda .pers{background:var(--bar-pass)}
.q{padding:18px 20px;margin:0 0 12px}.q h3{font-size:17px;line-height:1.4;margin:8px 0 10px;font-weight:600}
.q .meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:12px;color:var(--muted)}
.q .why{font-size:13.5px;color:var(--muted);margin:0 0 10px}
.q .quote{font-size:13.5px;font-style:italic;color:var(--muted);border-left:3px solid var(--border);padding-left:10px;margin:0 0 10px}
.cols{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.cols>div{background:var(--panel2);border-radius:10px;padding:8px 12px}.cols h4{margin:0 0 4px;font-size:12.5px}
.cols ul{margin:0;padding-left:18px;font-size:13.5px}
.cols .f h4{color:var(--blue)}.cols .l h4{color:var(--teal)}.cols .ws h4{color:var(--amber)}
.notes-box{border:1px dashed var(--border);border-radius:10px;height:64px;margin-top:10px}
.score{width:100%;border-collapse:collapse;font-size:13.5px}
.score th,.score td{border-top:1px solid var(--border);padding:8px 8px;text-align:left;vertical-align:top}
.score th{color:var(--muted);font-weight:600}
.box{display:inline-block;width:14px;height:14px;border:1.5px solid var(--muted);border-radius:4px;vertical-align:-2px;margin-right:6px}
.lvl{font-size:12.5px;color:var(--muted)}
.mini{font-size:13px;color:var(--muted)}
@media (max-width:640px){.cols{grid-template-columns:1fr}.score{font-size:12.5px}}
@media print{.q,.card{break-inside:avoid}.notes-box{height:90px}}
"""


def q_card(q, crit, personal):
    c = crit.get(q.get("criterion"), {})
    tags = [f'<span class="tier {e(c.get("tier", ""))}">{e(R.TIER_LABEL.get(c.get("tier"), ""))}</span>',
            f'<span>{e(c.get("name", q.get("criterion")))}</span>',
            f'<span>· {e(q.get("minutes"))} min</span>']
    if personal:
        tags.insert(0, f'<span class="tag pass">{e(TYPE_LABEL.get(q.get("type"), q.get("type")))}</span>')
    h = [f'<div class="card q"><div class="meta">{"".join(tags)}</div><h3>{e(q.get("question"))}</h3>']
    for ev in q.get("evidence", []) or []:
        h.append(f'<div class="quote">From the CV: “{e(ev)}”</div>')
    if q.get("why"):
        h.append(f'<p class="why"><strong>Why ask:</strong> {e(q["why"])}</p>')

    def lst(items):
        return "".join(f"<li>{e(x)}</li>" for x in items or []) or "<li>—</li>"
    h.append(f'<div class="cols"><div class="f"><h4>Follow-ups</h4><ul>{lst(q.get("follow_ups"))}</ul></div>'
             f'<div class="l"><h4>Strong answers include</h4><ul>{lst(q.get("listen_for"))}</ul></div>'
             f'<div class="ws"><h4>Warning signs</h4><ul>{lst(q.get("warning_signs"))}</ul></div></div>'
             '<div class="notes-box" aria-label="Notes"></div></div>')
    return "".join(h)


def build_html(rubric, core, kit, row, role_name):
    crit = {c["id"]: c for c in rubric["criteria"]}
    cid = kit["candidate_id"]
    core_q, pers_q = core.get("questions", []), kit.get("questions", [])
    core_m = sum(q.get("minutes", 0) for q in core_q)
    pers_m = sum(q.get("minutes", 0) for q in pers_q)
    dur = core.get("duration_minutes", core_m + pers_m) or 1
    spare = max(0, dur - core_m - pers_m)
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer">',
         '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; '
         'script-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\'">',
         f'<title>Interview kit · {e(cid)}</title><style>{R.CSS}{KIT_CSS}</style></head><body><div class="wrap">']
    sub = ""
    if row:
        sub = (f' · {e(row["file"])} · screening score {float(row["score"]):.1f} · '
               f'{e(R.GATE_LABEL.get(row["gate"], row["gate"]))}')
    h.append('<div class="top"><div><div class="muted">Interview kit · ' + e(role_name) + '</div>'
             f'<h1>{e(cid)}</h1><div class="muted">{e(core.get("stage", "interview"))} · {e(dur)} minutes{sub}</div></div>'
             '<button class="btn" id="theme" type="button" title="Switch between light and dark">Light / dark</button></div>')
    h.append('<div class="callout"><strong>For the interviewer.</strong> Ask every core question in order, so candidates '
             'can be compared fairly; then the personal questions. Rate each criterion afterwards against the anchors '
             'below. Don’t ask about age, family, nationality, health, religion or other personal characteristics.</div>')
    h.append(f'<div class="agenda" title="Time plan"><span class="core" style="width:{100*core_m/dur:.0f}%"></span>'
             f'<span class="pers" style="width:{100*pers_m/dur:.0f}%"></span></div>'
             f'<div class="legend"><span><i style="background:var(--blue)"></i>Core questions · {e(core_m)} min</span>'
             f'<span><i style="background:var(--bar-pass)"></i>Personal questions · {e(pers_m)} min</span>'
             f'<span><i style="background:var(--panel2)"></i>Candidate’s questions · {e(spare)} min</span></div>')
    notes = kit.get("notes_for_interviewer", [])
    if notes:
        h.append('<h2>Before you start</h2><div class="card notes"><ul>' + "".join(f"<li>{e(n)}</li>" for n in notes) + "</ul></div>")
    h.append('<h2>Core questions</h2><p class="mini">The same for every candidate.</p>')
    h += [q_card(q, crit, False) for q in core_q]
    h.append('<h2>Personal questions</h2><p class="mini">Based on this candidate’s CV.</p>')
    h += [q_card(q, crit, True) for q in pers_q]
    h.append('<h2>Scorecard</h2><p class="mini">Fill in after the interview, from the answers alone.</p>'
             '<div class="card" style="padding:6px 14px;overflow-x:auto"><table class="score"><thead><tr><th>Criterion</th>'
             '<th>0</th><th>1</th><th>2</th><th>3</th></tr></thead><tbody>')
    asked = {q.get("criterion") for q in core_q + pers_q}
    for c in rubric["criteria"]:
        if c["id"] not in asked:
            continue
        anchors = c.get("anchors", {})
        cells = "".join(f'<td><span class="box"></span><span class="lvl">{e(anchors.get(str(k), ""))}</span></td>' for k in range(4))
        h.append(f'<tr><td><span class="tier {e(c["tier"])}">{e(R.TIER_LABEL.get(c["tier"], ""))}</span><br>'
                 f'<strong>{e(c["name"])}</strong></td>{cells}</tr>')
    h.append('</tbody></table></div><h2>Overall notes</h2><div class="card" style="padding:14px"><div class="notes-box" style="height:120px;border:0"></div></div>')
    h.append('<footer>This kit contains candidate data and makes no network requests. Delete it when the round closes.</footer>')
    h.append(f'<script>{R.JS}</script></div></body></html>')
    return "".join(h)


def build_md(rubric, core, kit, row):
    crit = {c["id"]: c for c in rubric["criteria"]}
    out = [f"# Interview kit — {kit['candidate_id']}" + (f" ({row['file']})" if row else ""), "",
           f"{core.get('stage', 'interview')} · {core.get('duration_minutes')} minutes", ""]
    if kit.get("notes_for_interviewer"):
        out += ["## Before you start", ""] + [f"- {n}" for n in kit["notes_for_interviewer"]] + [""]
    for title, qs in (("Core questions (same for every candidate)", core.get("questions", [])),
                      ("Personal questions", kit.get("questions", []))):
        out += [f"## {title}", ""]
        for i, q in enumerate(qs, 1):
            c = crit.get(q.get("criterion"), {})
            kind = f" · {TYPE_LABEL.get(q['type'], q['type'])}" if q.get("type") else ""
            out += [f"### {i}. {q['question']}", "", f"*{c.get('name', q.get('criterion'))} · {q.get('minutes')} min{kind}*", ""]
            out += [f"> From the CV: “{ev}”" for ev in q.get("evidence", []) or []]
            if q.get("why"):
                out += ["", f"**Why ask:** {q['why']}"]
            out += ["", "**Follow-ups:** " + "; ".join(q.get("follow_ups", [])),
                    "", "**Strong answers include:** " + "; ".join(q.get("listen_for", [])),
                    "", "**Warning signs:** " + "; ".join(q.get("warning_signs", [])), ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role_dir")
    ap.add_argument("--candidates", nargs="*", default=None)
    args = ap.parse_args(argv)
    role = Path(args.role_dir)
    kdir = role / "interviews"
    rubric = H.load_json(role / "rubric.json")
    core = H.load_json(kdir / "core.json")
    ranking = H.load_json(role / "ranking.json") if (role / "ranking.json").exists() else {"ranked": [], "below_the_line": []}
    rows = {r["candidate_id"]: r for r in ranking["ranked"] + ranking["below_the_line"]}
    files = [kdir / f"{c}.json" for c in args.candidates] if args.candidates else \
        sorted(p for p in kdir.glob("*.json") if p.stem != "core")
    done = []
    for path in files:
        kit = H.load_json(path)
        row = rows.get(kit["candidate_id"])
        (kdir / f"{path.stem}.html").write_text(build_html(rubric, core, kit, row, rubric["role"]), encoding="utf-8")
        (kdir / f"{path.stem}.md").write_text(build_md(rubric, core, kit, row), encoding="utf-8")
        done.append((path.stem, row))
    items = "".join(f'<a class="row" href="{e(cid)}.html"><span class="rk">{e(R.rank_label(r)) if r else ""}</span>'
                    f'<span class="who">{e(cid)}<small>{e(r["file"]) if r else ""}</small></span><span></span><span></span>'
                    f'<span class="tags"><span class="tag">open kit</span></span></a>' for cid, r in done)
    index = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
             f'<title>Interview kits</title><style>{R.CSS}</style></head><body><div class="wrap">'
             f'<div class="muted">Interview kits</div><h1>{e(rubric["role"])}</h1>'
             f'<h2>Candidates</h2><div class="card shortlist">{items}</div></div></body></html>')
    (kdir / "index.html").write_text(index, encoding="utf-8")
    print(f"Rendered {len(done)} kits to {kdir} (open index.html)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
