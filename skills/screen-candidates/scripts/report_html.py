"""Self-contained HTML version of the screening report.

Design rules:
- No network requests of any kind (no CDN scripts, web fonts or remote images): the file holds
  candidate data and must be safe to open anywhere.
- Every value that comes from CVs, scores or files is HTML-escaped. CV text is untrusted.
- Works without JavaScript (all content visible); JS only adds filters, search and a theme toggle.
- Prints cleanly (light theme, every card expanded) so "Save as PDF" gives a shareable document.
"""
import re
from html import escape

TIER_LABEL = {"must_have": "Must", "important": "Important", "nice_to_have": "Nice"}
GATE_LABEL = {"pass": "Meets must-haves", "verify": "Verify must-haves", "fail": "Below the line"}
STATUS_LABEL = {"evidenced": "evidenced", "weak": "weak", "no_evidence": "no evidence", "contradicted": "contradicted"}


def e(x):
    return escape("" if x is None else str(x), quote=True)


def inline_md(text):
    """Escape, then allow **bold** and `code` only."""
    t = e(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def notes_html(md):
    if not md or not md.strip():
        return ""
    items, paras = [], []
    for line in md.strip().splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")):
            items.append(f"<li>{inline_md(line[2:])}</li>")
        elif line:
            paras.append(f"<p>{inline_md(line)}</p>")
    return "".join(paras) + (f"<ul>{''.join(items)}</ul>" if items else "")


def rank_label(r):
    if r["gate"] == "fail":
        return "—"
    return f"={r['rank']}" if r.get("tied") else str(r["rank"])


def has_injection(r):
    return any("injection" in str(f) for f in r.get("flags", []))


def donut(score, gate):
    c = 2 * 3.14159 * 26
    filled = max(0.0, min(100.0, float(score))) / 100 * c
    return (f'<svg class="donut" viewBox="0 0 64 64" aria-hidden="true">'
            f'<circle cx="32" cy="32" r="26" class="donut-track"/>'
            f'<circle cx="32" cy="32" r="26" class="donut-fill g-{e(gate)}" '
            f'stroke-dasharray="{filled:.1f} {c:.1f}" transform="rotate(-90 32 32)"/>'
            f'<text x="32" y="37" text-anchor="middle">{float(score):.0f}</text></svg>')


def pills(level):
    return "".join(f'<span class="pill{" on" if i < level else ""}"></span>' for i in range(3))


CSS = """
:root{--bg:#f6f8fa;--panel:#ffffff;--panel2:#f0f3f6;--border:#d0d7de;--text:#1f2328;--muted:#59636e;
--teal:#0f766e;--teal-bg:#ccfbf1;--amber:#b45309;--amber-bg:#fef3c7;--red:#b91c1c;--red-bg:#fee2e2;
--blue:#1d4ed8;--slate:#64748b;--bar-pass:#14b8a6;--bar-verify:#f59e0b;--bar-fail:#ef4444;
--h0:#eef1f4;--h1:#c7f0e8;--h1t:#134e4a;--h2:#5eead4;--h2t:#042f2e;--h3:#0d9488;--h3t:#ffffff;--shadow:0 1px 3px rgba(0,0,0,.08)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1117;--panel:#161b22;--panel2:#1c2330;
--border:#30363d;--text:#e6edf3;--muted:#8b949e;--teal:#5eead4;--teal-bg:#0f2f2c;--amber:#fbbf24;--amber-bg:#3a2a07;
--red:#f87171;--red-bg:#3b1d1d;--blue:#7dd3fc;--slate:#94a3b8;--bar-pass:#5eead4;--bar-verify:#fbbf24;--bar-fail:#f87171;
--h0:#1c2330;--h1:#134e4a;--h1t:#ccfbf1;--h2:#0f766e;--h2t:#f0fdfa;--h3:#5eead4;--h3t:#0d1117;--shadow:none}}
:root[data-theme="dark"]{--bg:#0d1117;--panel:#161b22;--panel2:#1c2330;--border:#30363d;--text:#e6edf3;--muted:#8b949e;
--teal:#5eead4;--teal-bg:#0f2f2c;--amber:#fbbf24;--amber-bg:#3a2a07;--red:#f87171;--red-bg:#3b1d1d;--blue:#7dd3fc;
--slate:#94a3b8;--bar-pass:#5eead4;--bar-verify:#fbbf24;--bar-fail:#f87171;--h0:#1c2330;--h1:#134e4a;--h2:#0f766e;
--h1t:#ccfbf1;--h2t:#f0fdfa;--h3:#5eead4;--h3t:#0d1117;--shadow:none}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 64px}
h1{font-size:28px;margin:0 0 4px}h2{font-size:20px;margin:40px 0 14px}h3{font-size:18px;margin:0}
.muted{color:var(--muted)}code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--panel2);padding:1px 5px;border-radius:5px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.btn{background:var(--panel);color:var(--text);border:1px solid var(--border);border-radius:999px;padding:6px 14px;font:inherit;font-size:14px;cursor:pointer}
.btn[aria-pressed="true"]{background:var(--text);color:var(--bg);border-color:var(--text)}
.callout{margin:18px 0 0;padding:12px 16px;border-radius:12px;background:var(--panel);border:1px solid var(--border);border-left:4px solid var(--blue);font-size:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:22px}
.tile{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:14px 16px;box-shadow:var(--shadow)}
.tile b{display:block;font-size:28px;line-height:1.1}.tile span{color:var(--muted);font-size:13px}
.tile.pass b{color:var(--teal)}.tile.verify b{color:var(--amber)}.tile.fail b{color:var(--red)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:16px;box-shadow:var(--shadow)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin:0 0 12px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.shortlist{padding:10px 8px}
.row{display:grid;grid-template-columns:44px minmax(150px,230px) 1fr 52px 300px;align-items:center;gap:12px;padding:7px 10px;border-radius:10px;color:inherit;text-decoration:none}
.row:hover{background:var(--panel2)}
.rk{color:var(--muted);font:600 14px ui-monospace,Menlo,monospace;text-align:right}
.who{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.who small{font-weight:400;color:var(--muted);margin-left:6px}
.track{display:block;height:16px;background:var(--panel2);border-radius:99px;overflow:hidden}
.bar{display:block;height:100%;border-radius:99px}.g-pass.bar{background:var(--bar-pass)}.g-verify.bar{background:var(--bar-verify)}.g-fail.bar{background:var(--bar-fail);opacity:.5}
.sc{font:600 14px ui-monospace,Menlo,monospace;text-align:right}
.tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{font-size:12px;font-weight:600;padding:2px 9px;border-radius:99px;border:1px solid var(--border);color:var(--muted);white-space:nowrap}
.tag.inj{color:var(--red);background:var(--red-bg);border-color:transparent}
.tag.pass{color:var(--teal);background:var(--teal-bg);border-color:transparent}
.tag.verify{color:var(--amber);background:var(--amber-bg);border-color:transparent}
.tag.fail{color:var(--red);background:var(--red-bg);border-color:transparent}
.line{display:flex;align-items:center;gap:10px;margin:8px 10px;color:var(--red);font-size:13px;font-weight:600}
.line:before,.line:after{content:"";flex:1;border-top:1px dashed var(--red);opacity:.6}
.heat{overflow-x:auto;padding:4px}
table.hm{border-collapse:separate;border-spacing:3px;font-size:13px;min-width:640px;width:100%}
.hm th{font-weight:600;color:var(--muted);text-align:center;padding:4px;vertical-align:bottom}
.hm th.c{writing-mode:vertical-rl;transform:rotate(180deg);height:210px;max-width:34px;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hm th.must{color:var(--red)}
.hm td{text-align:center;border-radius:6px;height:30px;min-width:34px;font-weight:600}
.hm td.nm{text-align:left;white-space:nowrap;padding:0 8px;font-weight:600;min-width:150px}
.hm td.sc{padding:0 8px}
.l0{background:var(--h0);color:var(--muted)}.l1{background:var(--h1);color:var(--h1t)}.l2{background:var(--h2);color:var(--h2t)}.l3{background:var(--h3);color:var(--h3t)}
.lx{background:var(--red-bg);color:var(--red)}
.rub{padding:6px 0}
.ru{display:grid;grid-template-columns:86px 1fr 140px;gap:12px;align-items:center;padding:10px 18px;border-top:1px solid var(--border)}
.ru:first-child{border-top:0}.ru p{margin:2px 0 0;font-size:13px;color:var(--muted)}
.w{height:8px;background:var(--panel2);border-radius:9px;overflow:hidden}.w i{display:block;height:100%;background:var(--blue)}
.tier{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:2px 8px;border-radius:99px;border:1px solid currentColor;justify-self:start}
.tier.must_have{color:var(--red)}.tier.important{color:var(--blue)}.tier.nice_to_have{color:var(--slate)}
.notes{padding:14px 20px}.notes ul{margin:6px 0;padding-left:20px}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 14px}
.controls input{flex:1;min-width:180px;background:var(--panel);color:var(--text);border:1px solid var(--border);border-radius:999px;padding:7px 14px;font:inherit;font-size:14px}
details.cand{margin:0 0 14px;scroll-margin-top:12px}
details.cand>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:16px;padding:16px 20px}
details.cand>summary::-webkit-details-marker{display:none}
.donut{width:58px;height:58px;flex:none}.donut-track{fill:none;stroke:var(--panel2);stroke-width:7}
.donut-fill{fill:none;stroke-width:7;stroke-linecap:round}.donut-fill.g-pass{stroke:var(--bar-pass)}.donut-fill.g-verify{stroke:var(--bar-verify)}.donut-fill.g-fail{stroke:var(--bar-fail)}
.donut text{font:700 17px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:var(--text)}
.sumtxt{flex:1;min-width:0}.sumtxt .tags{margin-top:6px}
.chev{color:var(--muted);transition:transform .15s}details[open] .chev{transform:rotate(90deg)}
.body{padding:0 20px 20px}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}
.sg>div{background:var(--panel2);border-radius:12px;padding:10px 14px}.sg h4{margin:0 0 4px;font-size:13px}
.sg ul{margin:0;padding-left:18px;font-size:14px}.sg .s h4{color:var(--teal)}.sg .g h4{color:var(--amber)}
.cr{display:grid;grid-template-columns:86px 1fr auto;gap:4px 12px;padding:10px 0;border-top:1px solid var(--border)}
.cr .nm{font-weight:600}.cr .lv{display:flex;gap:4px;align-items:center;justify-self:end}
.pill{display:inline-block;width:26px;height:10px;border-radius:9px;background:var(--panel2);border:1px solid var(--border)}.pill.on{background:var(--bar-pass);border-color:transparent}
.cr .ev{grid-column:2/4;font-size:13.5px;color:var(--muted);font-style:italic}
.cr .st{font-size:12px;color:var(--muted);margin-left:8px;font-style:normal}
.cr .st.contradicted{color:var(--red);font-weight:600}.cr .st.no_evidence{color:var(--amber)}
.probe{margin-top:14px;background:var(--panel2);border-radius:12px;padding:12px 16px}.probe h4{margin:0 0 6px;font-size:13px;color:var(--blue)}
.probe ol{margin:0;padding-left:20px}
.flags{margin-top:12px;padding:10px 14px;border-radius:12px;background:var(--red-bg);color:var(--red);font-size:14px}
.hidden{display:none!important}
footer{margin-top:44px;font-size:13px;color:var(--muted);border-top:1px solid var(--border);padding-top:16px}
footer ul{padding-left:18px}
@media (max-width:640px){.row{grid-template-columns:34px 1fr 50px;}.row .track{grid-column:2/4;grid-row:2}.row .tags{grid-column:2/4}
.sg{grid-template-columns:1fr}.ru{grid-template-columns:1fr}.cr{grid-template-columns:1fr auto}.cr .tier{grid-column:1/3}.cr .ev{grid-column:1/3}
details.cand>summary{padding:14px}.body{padding:0 14px 14px}}
@media print{:root{--bg:#fff;--panel:#fff;--panel2:#f3f4f6;--border:#d1d5db;--text:#111;--muted:#4b5563;--shadow:none}
.controls,.btn,.chev{display:none!important}.wrap{max-width:none;padding:0}details.cand{break-inside:avoid}
details.cand>.body{display:block!important}.hidden{display:block!important}h2{break-after:avoid}}
"""

JS = """
(function(){
  var root=document.documentElement, KEY='rah-theme';
  try{var t=localStorage.getItem(KEY); if(t) root.setAttribute('data-theme',t);}catch(e){}
  var tb=document.getElementById('theme');
  if(tb) tb.addEventListener('click',function(){
    var dark=root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);
    var next=dark?'light':'dark'; root.setAttribute('data-theme',next);
    try{localStorage.setItem(KEY,next);}catch(e){}
  });
  var cards=[].slice.call(document.querySelectorAll('details.cand'));
  var filter='all', q='';
  function apply(){
    cards.forEach(function(c){
      var okF = filter==='all' || c.dataset.gate===filter || (filter==='flagged' && c.dataset.flag==='1');
      var okQ = !q || c.textContent.toLowerCase().indexOf(q)>=0;
      c.classList.toggle('hidden', !(okF&&okQ));
    });
  }
  [].forEach.call(document.querySelectorAll('[data-filter]'),function(b){
    b.addEventListener('click',function(){
      filter=b.dataset.filter;
      [].forEach.call(document.querySelectorAll('[data-filter]'),function(x){x.setAttribute('aria-pressed', x===b?'true':'false');});
      apply();
    });
  });
  var s=document.getElementById('search'); if(s) s.addEventListener('input',function(){q=s.value.trim().toLowerCase();apply();});
  var ex=document.getElementById('expand');
  if(ex) ex.addEventListener('click',function(){
    var open=!cards.every(function(c){return c.open;}); cards.forEach(function(c){c.open=open;});
    ex.textContent=open?'Collapse all':'Expand all';
  });
  [].forEach.call(document.querySelectorAll('a[href^="#cand-"]'),function(a){
    a.addEventListener('click',function(){var d=document.querySelector(a.getAttribute('href')); if(d) d.open=true;});
  });
  window.addEventListener('beforeprint',function(){cards.forEach(function(c){c.open=true;});});
})();
"""


def build_html(rubric, ranking, scores, notes_md="", date=""):
    crit = rubric["criteria"]
    rows = ranking["ranked"] + ranking["below_the_line"]
    n = len(rows)
    n_pass = sum(1 for r in rows if r["gate"] == "pass")
    n_ver = sum(1 for r in rows if r["gate"] == "verify")
    n_fail = sum(1 for r in rows if r["gate"] == "fail")
    n_flag = sum(1 for r in rows if r.get("flags"))
    max_w = max([c.get("weight", 0) for c in crit if c["tier"] != "must_have"] + [1])

    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<meta name="referrer" content="no-referrer">',
         # CSP: nothing may load from the network; only this file's own styles and script run.
         '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; '
         'script-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\'">',
         f'<title>Screening report · {e(rubric["role"])}</title><style>{CSS}</style></head><body><div class="wrap">']

    h.append('<div class="top"><div>'
             f'<div class="muted">Screening report</div><h1>{e(rubric["role"])}</h1>'
             f'<div class="muted">Rubric v{e(rubric.get("version"))} · approved by {e(rubric.get("approved_by") or "—")} · '
             f'{e(date)} · {n} candidates'
             + (f' · focus {e(rubric["focus_version"])}' if rubric.get("focus_version") else "")
             + ('<br>Scope: ' + e(", ".join(f"{k} {float(v):.0%}" for k, v in rubric["scope"].items()))
                if isinstance(rubric.get("scope"), dict) and rubric["scope"] else "")
             + '</div></div>'
             '<button class="btn" id="theme" type="button" title="Switch between light and dark">Light / dark</button></div>')
    h.append('<div class="callout"><strong>Decision support only.</strong> This report ranks CV evidence against an '
             'approved rubric. It does not reject or advance anyone. A named person reads the evidence and decides. '
             '“No evidence” means the CV doesn’t show it, not that the person can’t do it: use the interview probes.</div>')

    h.append('<div class="tiles">'
             f'<div class="tile"><b>{n}</b><span>candidates screened</span></div>'
             f'<div class="tile pass"><b>{n_pass}</b><span>meet every must-have</span></div>'
             f'<div class="tile verify"><b>{n_ver}</b><span>must-have to verify</span></div>'
             f'<div class="tile fail"><b>{n_fail}</b><span>below the line</span></div>'
             f'<div class="tile"><b>{n_flag}</b><span>flagged for review</span></div></div>')

    # shortlist
    h.append('<h2>Shortlist</h2><div class="legend">'
             '<span><i style="background:var(--bar-pass)"></i>Meets every must-have</span>'
             '<span><i style="background:var(--bar-verify)"></i>Must-have not shown in CV: verify in interview</span>'
             '<span><i style="background:var(--bar-fail)"></i>CV contradicts a must-have</span></div>'
             '<div class="card shortlist">')
    for i, r in enumerate(rows):
        if r["gate"] == "fail" and (i == 0 or rows[i - 1]["gate"] != "fail"):
            h.append('<div class="line">below the line</div>')
        tags = [f'<span class="tag">{e(r.get("confidence", ""))} confidence</span>']
        if has_injection(r):
            tags.append('<span class="tag inj">⚠ injection flagged</span>')
        elif r.get("flags"):
            tags.append('<span class="tag inj">⚠ flagged</span>')
        h.append(f'<a class="row" href="#cand-{e(r["candidate_id"])}">'
                 f'<span class="rk">{e(rank_label(r))}</span>'
                 f'<span class="who">{e(r["candidate_id"])}<small>{e(r["file"])}</small></span>'
                 f'<span class="track"><span class="bar g-{e(r["gate"])}" style="width:{max(2.0, float(r["score"])):.1f}%"></span></span>'
                 f'<span class="sc">{float(r["score"]):.1f}</span>'
                 f'<span class="tags">{"".join(tags)}</span></a>')
    h.append('</div>')

    # heatmap
    h.append('<h2>At a glance</h2><p class="muted">Rubric level per criterion (0–3). '
             '<span style="color:var(--red)">✕</span> = CV contradicts it. Must-have columns are in red.</p>'
             '<div class="card heat"><table class="hm"><thead><tr><th></th>')
    for c in crit:
        cls = "c must" if c["tier"] == "must_have" else "c"
        h.append(f'<th class="{cls}" title="{e(c["name"])}">{e(c["name"][:34] + ("…" if len(c["name"]) > 34 else ""))}</th>')
    h.append('<th>Score</th></tr></thead><tbody>')
    for r in rows:
        s = scores.get(r["candidate_id"], {}).get("criteria", {})
        h.append(f'<tr><td class="nm">{e(rank_label(r))} · {e(r["candidate_id"])}</td>')
        for c in crit:
            ent = s.get(c["id"], {})
            lvl, st = ent.get("level", 0), ent.get("status", "no_evidence")
            if st == "contradicted":
                h.append(f'<td class="lx" title="{e(c["name"])}: contradicted">✕</td>')
            else:
                h.append(f'<td class="l{int(lvl) if lvl in (0, 1, 2, 3) else 0}" title="{e(c["name"])}: {e(lvl)}/3 ({e(STATUS_LABEL.get(st, st))})">'
                         f'{e(lvl) if lvl else "·"}</td>')
        h.append(f'<td class="sc">{float(r["score"]):.0f}</td></tr>')
    h.append('</tbody></table></div>')

    # rubric
    h.append('<h2>Rubric</h2><div class="card rub">')
    for c in crit:
        w = c.get("weight", 0)
        right = ('<span class="muted" style="font-size:13px">gate, not points</span>' if c["tier"] == "must_have" else
                 f'<div><div class="w"><i style="width:{100 * w / max_w:.0f}%"></i></div>'
                 f'<span class="muted" style="font-size:12px">weight {e(w)}</span></div>')
        why = f'<p>{e(c.get("justification"))}</p>' if c.get("justification") else ""
        h.append(f'<div class="ru"><span class="tier {e(c["tier"])}">{e(TIER_LABEL.get(c["tier"], c["tier"]))}</span>'
                 f'<div><strong>{e(c["name"])}</strong>{why}</div>{right}</div>')
    h.append('</div>')

    nh = notes_html(notes_md)
    if nh:
        h.append(f'<h2>Worth noticing</h2><div class="card notes">{nh}</div>')

    # candidates
    h.append('<h2>Candidates</h2><div class="controls">'
             '<button class="btn" data-filter="all" aria-pressed="true" type="button">All</button>'
             '<button class="btn" data-filter="pass" aria-pressed="false" type="button">Meets must-haves</button>'
             '<button class="btn" data-filter="verify" aria-pressed="false" type="button">Verify</button>'
             '<button class="btn" data-filter="fail" aria-pressed="false" type="button">Below the line</button>'
             '<button class="btn" data-filter="flagged" aria-pressed="false" type="button">Flagged</button>'
             '<input id="search" type="search" placeholder="Search evidence, skills…" aria-label="Search candidates">'
             '<button class="btn" id="expand" type="button">Expand all</button></div>')
    for i, r in enumerate(rows):
        s = scores.get(r["candidate_id"], {})
        gate_note = ""
        if r.get("gate_notes"):
            gate_note = f'<div class="muted" style="font-size:13px;margin-top:4px">{e("; ".join(r["gate_notes"]))}</div>'
        flag = "1" if r.get("flags") else "0"
        tags = [f'<span class="tag {e(r["gate"])}">{e(GATE_LABEL[r["gate"]])}</span>',
                f'<span class="tag">{"rank " + e(rank_label(r)) if r["gate"] != "fail" else "unranked"}</span>',
                f'<span class="tag">{e(r.get("confidence", ""))} confidence</span>']
        if has_injection(r):
            tags.append('<span class="tag inj">⚠ injection flagged</span>')
        h.append(f'<details class="card cand" id="cand-{e(r["candidate_id"])}" data-gate="{e(r["gate"])}" data-flag="{flag}"{" open" if i < 3 else ""}>'
                 f'<summary>{donut(r["score"], r["gate"])}<div class="sumtxt"><h3>{e(r["candidate_id"])} '
                 f'<span class="muted" style="font-weight:400;font-size:15px">· {e(r["file"])}</span></h3>'
                 f'<div class="tags">{"".join(tags)}</div>{gate_note}</div><span class="chev">▶</span></summary><div class="body">')
        st_items = "".join(f"<li>{e(x)}</li>" for x in s.get("strengths", [])) or "<li>—</li>"
        gp_items = "".join(f"<li>{e(x)}</li>" for x in s.get("gaps", [])) or "<li>—</li>"
        h.append(f'<div class="sg"><div class="s"><h4>Strengths</h4><ul>{st_items}</ul></div>'
                 f'<div class="g"><h4>Gaps / no evidence</h4><ul>{gp_items}</ul></div></div>')
        for c in crit:
            ent = s.get("criteria", {}).get(c["id"], {})
            lvl, st = ent.get("level", 0), ent.get("status", "no_evidence")
            ev = ent.get("evidence", [])
            ev_html = " ".join(f"“{e(x)}”" for x in ev) if ev else "No evidence in the CV: probe in interview."
            h.append(f'<div class="cr"><span class="tier {e(c["tier"])}">{e(TIER_LABEL.get(c["tier"], c["tier"]))}</span>'
                     f'<span class="nm">{e(c["name"])}</span>'
                     f'<span class="lv">{pills(int(lvl) if isinstance(lvl, int) else 0)}<span class="muted" style="font:600 12px ui-monospace,Menlo,monospace;margin-left:4px">{e(lvl)}/3</span></span>'
                     f'<span class="ev">{ev_html}<span class="st {e(st)}">· {e(STATUS_LABEL.get(st, st))}</span></span></div>')
        probes = "".join(f"<li>{e(p)}</li>" for p in s.get("interview_probes", []))
        if probes:
            h.append(f'<div class="probe"><h4>Interview probes, grounded in the repo</h4><ol>{probes}</ol></div>')
        if s.get("flags"):
            h.append('<div class="flags"><strong>Flags:</strong> ' + "; ".join(e(f) for f in s["flags"]) + '</div>')
        h.append('</div></details>')

    h.append('<footer><strong>Method.</strong><ul>'
             '<li>CVs were extracted and redacted (name, contact details, links, age, nationality), names were confirmed, '
             'and redaction was verified before scoring.</li>'
             '<li>Each CV was scored alone against the rubric; candidates were not compared while scoring.</li>'
             '<li>Every evidence quote was checked against the candidate’s redacted CV by <code>validate_scores.py</code>.</li>'
             '<li>Totals and order come from <code>rank.py</code>: score = Σ (level ÷ 3 × weight) over weighted criteria. '
             'Must-haves are gates; “verify” candidates rank after those who meet every must-have.</li></ul>'
             '<p>This file contains personal data and makes no network requests. Delete it when the round closes.</p></footer>')
    h.append(f'<script>{JS}</script></div></body></html>')
    return "".join(h)
