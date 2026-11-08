#!/usr/bin/env python3
"""Regenerate the README images from a fresh demo run, so they always show real output.

Usage: python3 docs/assets/make_assets.py

Writes docs/assets/{hero,shortlist,candidate-card,terminal,jd}.svg. Standard library only.
The two flow diagrams are rendered separately from their .mmd sources by render_diagrams.sh.
"""
import json
import re
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED = "#e6edf3", "#8b949e"
TEAL, AMBER, SLATE, RED, BLUE = "#5eead4", "#fbbf24", "#94a3b8", "#f87171", "#7dd3fc"


def run_demo():
    tmp = Path(tempfile.mkdtemp()) / "demo"
    out = subprocess.run([sys.executable, "-I", str(ROOT / "demo" / "run_demo.py"), str(tmp)],
                         capture_output=True, text=True, check=True).stdout
    ranking = json.loads((tmp / "ranking.json").read_text())
    rubric = json.loads((tmp / "rubric.json").read_text())
    scores = {p.stem: json.loads(p.read_text()) for p in (tmp / "scores").glob("*.json")}
    return out, ranking, rubric, scores


def display_name(fname):
    stem = fname.rsplit(".", 1)[0]
    parts = stem.split("-")
    return f"{parts[0].capitalize()} {parts[1][0].upper()}." if len(parts) > 1 else stem


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>{body}</svg>\n')


def text(x, y, s, size=14, fill=TEXT, weight=400, family=FONT, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


def clip(s, n):
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"

# ------------------------------------------------------------------ hero


def hero():
    w, h = 1280, 420
    b = [f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
         f'<stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#132036"/></linearGradient>'
         f'<radialGradient id="glow" cx="0.2" cy="0.3" r="0.6"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.18"/>'
         f'<stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{w}" height="{h}" rx="24" fill="url(#g)"/>',
         f'<rect width="{w}" height="{h}" rx="24" fill="url(#glow)"/>']
    # icon: repo tree feeding ranked bars
    ox, oy = 92, 118
    b.append(f'<rect x="{ox-28}" y="{oy-38}" width="236" height="236" rx="44" fill="#1e293b" stroke="{BORDER}"/>')
    for i, y in enumerate((oy + 10, oy + 80, oy + 150)):
        b.append(f'<line x1="{ox+12}" y1="{y}" x2="{ox+80}" y2="{y}" stroke="{TEAL}" stroke-width="12" stroke-linecap="round"/>')
        b.append(f'<circle cx="{ox+90}" cy="{y}" r="18" fill="{TEAL}"/>')
        bw = (66, 48, 26)[i]
        b.append(f'<rect x="{ox+124}" y="{y-14}" width="{bw}" height="28" rx="14" fill="{AMBER if i == 0 else SLATE}"/>')
    b.append(f'<line x1="{ox+12}" y1="{oy+10}" x2="{ox+12}" y2="{oy+150}" stroke="{TEAL}" stroke-width="12" stroke-linecap="round"/>')

    tx = 360
    b.append(text(tx, 150, "repo-aware-hiring", 54, TEXT, 700))
    b.append(text(tx, 202, "Hire for the codebase you actually have.", 30, TEAL, 600))
    b.append(text(tx, 248, "Agent skills that read your repo to write the job description, screen CVs", 19, MUTED))
    b.append(text(tx, 276, "with quoted evidence, and prepare a tailored interview for each candidate.", 19, MUTED))
    chips = ["Job descriptions", "Evidence-verified screening", "Interview kits", "Never auto-rejects"]
    x = tx
    for c in chips:
        cw = 16 + len(c) * 8.4
        b.append(f'<rect x="{x}" y="318" width="{cw:.0f}" height="36" rx="18" fill="#0f172a" stroke="{BORDER}"/>')
        b.append(text(x + cw / 2, 341, c, 15, TEXT, 500, anchor="middle"))
        x += cw + 12
    return svg(w, h, "".join(b), "repo-aware-hiring: hire for the codebase you actually have")

# ------------------------------------------------------------------ shortlist chart


def shortlist(ranking):
    rows = ranking["ranked"] + ranking["below_the_line"]
    w = 960
    top, rowh, gap = 112, 40, 34
    n_fail = len(ranking["below_the_line"])
    h = top + rowh * len(rows) + (gap if n_fail else 0) + 92
    bar_x, bar_w = 270, 470
    b = [f'<rect width="{w}" height="{h}" rx="16" fill="{BG}" stroke="{BORDER}"/>',
         text(32, 46, "Shortlist from the demo run", 22, TEXT, 700),
         text(32, 74, f"{ranking['role']} · rubric v{ranking['rubric_version']} · 12 fictional candidates", 14, MUTED)]
    legend = [(TEAL, "Meets every must-have"), (AMBER, "Must-have not shown in CV: verify"), (RED, "CV contradicts a must-have")]
    lx = 32
    for color, label in legend:
        b.append(f'<rect x="{lx}" y="86" width="12" height="12" rx="3" fill="{color}"/>')
        b.append(text(lx + 18, 97, label, 13, MUTED))
        lx += 34 + len(label) * 6.9
    y = top
    for i, r in enumerate(rows):
        if r["gate"] == "fail" and (i == 0 or rows[i - 1]["gate"] != "fail"):
            ly = y + 10
            b.append(f'<line x1="24" y1="{ly}" x2="{w-24}" y2="{ly}" stroke="{RED}" stroke-dasharray="6 6" stroke-opacity="0.6"/>')
            b.append(f'<rect x="{w/2-70}" y="{ly-11}" width="140" height="22" rx="11" fill="{BG}"/>')
            b.append(text(w / 2, ly + 5, "below the line", 13, RED, 600, anchor="middle"))
            y += gap
        rank = "—" if r["gate"] == "fail" else (f"={r['rank']}" if r.get("tied") else str(r["rank"]))
        color = {"pass": TEAL, "verify": AMBER, "fail": RED}[r["gate"]]
        b.append(text(44, y + 25, rank, 15, MUTED, 600, MONO, "end"))
        b.append(text(60, y + 25, f"{r['candidate_id']}  {display_name(r['file'])}", 15, TEXT, 500))
        b.append(f'<rect x="{bar_x}" y="{y+10}" width="{bar_w}" height="20" rx="10" fill="{PANEL}"/>')
        bw = max(6, bar_w * r["score"] / 100)
        b.append(f'<rect x="{bar_x}" y="{y+10}" width="{bw:.1f}" height="20" rx="10" fill="{color}" fill-opacity="{0.45 if r["gate"] == "fail" else 0.95}"/>')
        b.append(text(bar_x + bar_w + 14, y + 25, f"{r['score']:.1f}", 15, MUTED if r["gate"] == "fail" else TEXT, 600, MONO))
        if any("injection" in f for f in r["flags"]):
            bx = bar_x + bar_w + 74
            b.append(f'<rect x="{bx}" y="{y+8}" width="110" height="24" rx="12" fill="#3b1d1d" stroke="{RED}" stroke-opacity="0.6"/>')
            b.append(text(bx + 55, y + 25, "⚠ injection", 12, RED, 600, anchor="middle"))
        y += rowh
    fy = h - 44
    b.append(text(32, fy, "Score = weighted rubric levels out of 100. Must-haves are gates, not points. Ties are marked “=”.", 13, MUTED))
    b.append(text(32, fy + 22, "Each score is backed by quotes from the CV in report.md. Nothing here rejects anyone: humans decide.", 13, MUTED))
    return svg(w, h, "".join(b), "Bar chart of the demo shortlist with must-have gates and injection flags")

# ------------------------------------------------------------------ candidate card


def candidate_card(ranking, rubric, scores):
    top = ranking["ranked"][0]
    s = scores[top["candidate_id"]]
    crit = rubric["criteria"]
    w = 960
    rowh = 58
    y0 = 150
    h = y0 + rowh * len(crit) + 150
    b = [f'<rect width="{w}" height="{h}" rx="16" fill="{BG}" stroke="{BORDER}"/>',
         text(32, 48, f"{top['candidate_id']} · {display_name(top['file'])}", 24, TEXT, 700),
         text(32, 76, f"Rank #{top['rank']} · {top['score']}/100 · all must-haves met", 15, TEAL, 600),
         text(32, 110, "Strength: " + clip(s["strengths"][0], 92), 14, TEXT),
         text(32, 132, "Gap: " + clip(s["gaps"][0], 96), 14, AMBER)]
    for i, c in enumerate(crit):
        y = y0 + i * rowh
        e = s["criteria"][c["id"]]
        tier = {"must_have": "MUST", "important": "IMP", "nice_to_have": "NICE"}[c["tier"]]
        tcol = {"MUST": RED, "IMP": BLUE, "NICE": SLATE}[tier]
        b.append(f'<rect x="32" y="{y+4}" width="48" height="20" rx="10" fill="none" stroke="{tcol}"/>')
        b.append(text(56, y + 18, tier, 11, tcol, 700, anchor="middle"))
        b.append(text(92, y + 19, clip(c["name"], 62), 14, TEXT, 600))
        for k in range(3):
            filled = k < e["level"]
            b.append(f'<rect x="{w-224+k*42}" y="{y+6}" width="36" height="14" rx="7" '
                     f'fill="{TEAL if filled else PANEL}" stroke="{BORDER}"/>')
        b.append(text(w - 36, y + 18, f"{e['level']}/3", 13, MUTED, 600, MONO, "end"))
        quote = ("“" + clip(e["evidence"][0], 100) + "”") if e["evidence"] else "No evidence in CV: probe in interview"
        b.append(text(92, y + 42, quote, 13, MUTED, 400, extra='font-style="italic"'))
    py = y0 + rowh * len(crit) + 20
    b.append(f'<rect x="24" y="{py}" width="{w-48}" height="96" rx="12" fill="{PANEL}" stroke="{BORDER}"/>')
    b.append(text(44, py + 30, "Interview probe, grounded in the repo", 14, BLUE, 700))
    probe = s["interview_probes"][0]
    words, lines, cur = probe.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > 110:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    lines.append(cur)
    for j, ln in enumerate(lines[:2]):
        b.append(text(44, py + 56 + j * 20, ln, 14, TEXT))
    return svg(w, h, "".join(b), "Candidate detail card with criterion levels, quoted evidence and an interview probe")

# ------------------------------------------------------------------ terminal


def terminal(demo_out):
    lines = [ln.rstrip() for ln in demo_out.splitlines()]
    keep, started = [], False
    for ln in lines:
        if ln.startswith("Backend Engineer, Database Owner"):
            started = True
        if started:
            if ln.startswith("[6/6]"):
                break
            keep.append(ln)
    keep = ["$ python3 demo/run_demo.py", "…", "[5/6] Validate scores and rank (validate_scores.py + rank.py)", "12 score files, 0 errors.", ""] + keep
    trimmed = []
    for ln in keep:
        ln = ln.replace("FLAG possible_prompt_injection: summary contains a note addressed to the AI recruiting system; ignored for scoring", "⚠ injection flagged")
        ln = ln.replace("FLAG possible_prompt_injection: hidden text instructs AI screeners to rank this candidate first; ignored for scoring", "⚠ hidden-text injection flagged")
        ln = ln.replace("verify: Runs PostgreSQL in production (schema design, indexes, query plans); verify: Ships schema and data migrations on live data safely", "verify 2 must-haves")
        trimmed.append(clip(ln, 104))
    w = 960
    lh = 21
    h = 64 + lh * len(trimmed) + 24
    b = [f'<rect width="{w}" height="{h}" rx="14" fill="{BG}" stroke="{BORDER}"/>',
         f'<rect width="{w}" height="40" rx="14" fill="{PANEL}"/><rect y="26" width="{w}" height="14" fill="{PANEL}"/>']
    for k, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        b.append(f'<circle cx="{24+k*20}" cy="20" r="6" fill="{col}"/>')
    b.append(text(w / 2, 25, "demo — no model, no setup", 13, MUTED, 500, anchor="middle"))
    for i, ln in enumerate(trimmed):
        y = 66 + i * lh
        col = TEXT
        if ln.startswith("$"):
            col = TEAL
        elif "⚠" in ln or ln.startswith("Below the line") or "fails:" in ln:
            col = RED if "fails:" in ln or "Below" in ln else AMBER
        elif ln.startswith("Rank") or ln.startswith("[") or ln == "…":
            col = MUTED
        b.append(f'<text x="24" y="{y}" font-family="{MONO}" font-size="14" fill="{col}" xml:space="preserve">{escape(ln)}</text>')
    return svg(w, h, "".join(b), "Terminal output of the demo: validated, ranked candidates with flags")


# ------------------------------------------------------------------ job description visual

JD_PAIRS = [  # the translations write-job-description documents and applies
    ("Migrations run in backend/scripts/prestart.sh on every container start",
     "Make our schema changes safe to ship without downtime"),
    ("No backups or replication configured for the database",
     "Own the reliability of our PostgreSQL databases"),
    ("OFFSET pagination on the items endpoint is slow",
     "Find and fix performance problems as our data grows"),
]


def jd_check_output():
    tmp = Path(tempfile.mkdtemp()) / "role"
    tmp.mkdir()
    fx = ROOT / "evals" / "fixtures" / "db-owner"
    for name in ("repo-profile.md", "brief.md", "rubric.json"):
        (tmp / name).write_text((fx / name).read_text())
    out = subprocess.run([sys.executable, "-I", str(ROOT / "skills" / "write-job-description" / "scripts" / "check_jd.py"),
                          str(tmp), "--jd", str(ROOT / "evals" / "fixtures" / "jd" / "bad-jd.md")],
                         capture_output=True, text=True).stdout
    return out


def jd_visual():
    out = jd_check_output()
    lines = [ln for ln in out.splitlines() if ln.startswith(("ERROR", "warn"))]
    pick = []
    for key in ("file path", "security weakness", "environment variable", "internal detail", "years-of-experience",
                "native speaker", "must-haves: keep", "rubric must-have not"):
        for ln in lines:
            if key in ln and ln not in pick:
                pick.append(ln)
                break
    summary = [ln for ln in out.splitlines() if ln.endswith("warnings.")][0]
    w = 960
    rowh = 74
    top = 104
    h = top + rowh * len(JD_PAIRS) + 64 + 26 * (len(pick) + 2) + 40
    b = [f'<rect width="{w}" height="{h}" rx="16" fill="{BG}" stroke="{BORDER}"/>',
         text(32, 46, "From your code to a public job posting", 22, TEXT, 700),
         text(32, 74, "write-job-description describes the real work, in words that are safe to publish", 14, MUTED),
         text(32, top - 8, "IN YOUR REPO (STAYS PRIVATE)", 12, RED, 700),
         text(w / 2 + 24, top - 8, "IN THE JOB POSTING (PUBLIC)", 12, TEAL, 700)]
    colw = w / 2 - 56
    for i, (priv, pub) in enumerate(JD_PAIRS):
        y = top + i * rowh
        b.append(f'<rect x="24" y="{y}" width="{colw}" height="{rowh-14}" rx="10" fill="{PANEL}" stroke="#4c2626"/>')
        b.append(f'<rect x="{w/2+16}" y="{y}" width="{colw}" height="{rowh-14}" rx="10" fill="{PANEL}" stroke="#134e4a"/>')
        for j, part in enumerate(_wrap(priv, 48)[:2]):
            b.append(text(40, y + 25 + j * 19, part, 14, MUTED))
        for j, part in enumerate(_wrap(pub, 50)[:2]):
            b.append(text(w / 2 + 32, y + 25 + j * 19, part, 15, TEXT, 600))
        b.append(text(w / 2, y + 36, "→", 22, AMBER, 700, anchor="middle"))
    ty = top + rowh * len(JD_PAIRS) + 22
    th = 26 * (len(pick) + 2) + 30
    b.append(f'<rect x="24" y="{ty}" width="{w-48}" height="{th}" rx="12" fill="#0b0f14" stroke="{BORDER}"/>')
    b.append(f'<text x="44" y="{ty+30}" font-family="{MONO}" font-size="13" fill="{TEAL}">$ check_jd.py   # on a posting written without the skill</text>')
    for k, ln in enumerate(pick):
        col = RED if ln.startswith("ERROR") else AMBER
        ln = re.sub(r"\s+line\s+(\S+):", r" line \1:", ln).replace(" (say what the hire will build instead)", "")
        b.append(f'<text x="44" y="{ty+56+k*26}" font-family="{MONO}" font-size="13" fill="{col}" xml:space="preserve">{escape(clip(ln, 104))}</text>')
    b.append(f'<text x="44" y="{ty+56+len(pick)*26}" font-family="{MONO}" font-size="13" fill="{MUTED}">{escape(summary)} Errors block publishing.</text>')
    return svg(w, h, "".join(b), "Repo findings translated into public job-posting language, with checker output")


def _wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > n:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    return lines + [cur]


def main():
    demo_out, ranking, rubric, scores = run_demo()
    (HERE / "hero.svg").write_text(hero(), encoding="utf-8")
    (HERE / "shortlist.svg").write_text(shortlist(ranking), encoding="utf-8")
    (HERE / "candidate-card.svg").write_text(candidate_card(ranking, rubric, scores), encoding="utf-8")
    (HERE / "terminal.svg").write_text(terminal(demo_out), encoding="utf-8")
    (HERE / "jd.svg").write_text(jd_visual(), encoding="utf-8")
    print("Wrote hero.svg, shortlist.svg, candidate-card.svg, terminal.svg, jd.svg")


if __name__ == "__main__":
    main()
