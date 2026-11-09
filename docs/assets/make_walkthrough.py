#!/usr/bin/env python3
"""Animated SVG of an agent session drafting a job description (based on the Ollama test run).

Usage: python3 docs/assets/make_walkthrough.py   -> docs/assets/walkthrough.svg
Pure SVG + CSS, no scripts (GitHub renders it in an <img>). Loops; shows everything at once for people who
prefer reduced motion. Standard library only.
"""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = 520
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED, TEAL, AMBER, BLUE = "#e6edf3", "#8b949e", "#5eead4", "#fbbf24", "#7dd3fc"

# (text, colour, seconds after start when the line appears)
LINES = [
    ("> Draft a job description for a", AMBER, 0.4),
    ("  senior inference-engine engineer", AMBER, 0.4),
    ("● Read the codebase map:", MUTED, 1.6),
    ("  30 model architectures, 2 engines", MUTED, 1.6),
    ("● What should be true after a year?", TEXT, 2.8),
    ("  A) Measurably faster generation", BLUE, 3.3),
    ("  B) New models run well on day one", BLUE, 3.6),
    ("  C) Write my own answer", BLUE, 3.9),
    ("  D) Skip", BLUE, 4.2),
    ("> B", AMBER, 5.4),
    ("● Recorded. Pay, location: skipped", MUTED, 6.2),
    ("  → [insert: …] placeholders", MUTED, 6.2),
    ("● Drafting: the work, not the code …", TEXT, 8.0),
    ("✓ check_jd: 0 leaked internals", TEAL, 9.8),
    ("✓ jd.md: a draft for you to finish", TEAL, 10.8),
]
LOOP = 16.0
LINE_H, TOP, LEFT, SIZE = 27, 66, 20, 17


def main():
    h = TOP + LINE_H * len(LINES) + 24
    css = [f".l{{opacity:0;animation:none {LOOP}s infinite}}",
           "@media (prefers-reduced-motion: reduce){.l{opacity:1 !important;animation:none !important}}"]
    body = [f'<rect width="{W}" height="{h}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
            f'<rect width="{W}" height="40" rx="12" fill="{PANEL}"/><rect y="28" width="{W}" height="12" fill="{PANEL}"/>',
            *[f'<circle cx="{22 + i * 18}" cy="20" r="6" fill="{c}"/>' for i, c in enumerate(("#f87171", AMBER, "#4ade80"))],
            f'<text x="{W / 2}" y="25" font-family="{MONO}" font-size="13" fill="{MUTED}" text-anchor="middle">'
            f'example run on Ollama\'s public repo (unofficial)</text>']
    for i, (s, colour, t) in enumerate(LINES):
        start = t / LOOP * 100
        fade_in = min(start + 2.5, 94)
        css.append(f"@keyframes k{i}{{0%,{start:.2f}%{{opacity:0}}{fade_in:.2f}%,94%{{opacity:1}}100%{{opacity:0}}}}"
                   f".l{i}{{animation-name:k{i}}}")
        body.append(f'<text class="l l{i}" x="{LEFT}" y="{TOP + i * LINE_H}" font-family="{MONO}" font-size="{SIZE}" '
                    f'fill="{colour}" xml:space="preserve">{escape(s)}</text>')
    title = ("Animated example: the agent reads the codebase map, asks a multiple-choice question with write-your-own "
             "and skip options, records a skip as none, and drafts a job description that passes the leak check")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" '
           f'aria-label="{escape(title)}"><title>{escape(title)}</title><style>{"".join(css)}</style>{"".join(body)}</svg>\n')
    (HERE / "walkthrough.svg").write_text(svg, encoding="utf-8")
    print(f"wrote {HERE / 'walkthrough.svg'} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
