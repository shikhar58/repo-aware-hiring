"""Optional interview panel: which interviewer asks which questions.

core.json may contain
    "panel": [{"interviewer": "Payments lead", "criteria": ["c1", "c3"], "minutes": 30}, ...]
Each question goes to the interviewer whose criteria include the question's criterion; a question can override
that with its own "interviewer" field. Without a panel, one interviewer asks everything.
"""


def assign(core, questions):
    """-> ({question_index: interviewer or None}, problems[list of str])"""
    panel = core.get("panel") or []
    by_crit, problems = {}, []
    for p in panel:
        for c in p.get("criteria", []) or []:
            if c in by_crit and by_crit[c] != p.get("interviewer"):
                problems.append(f"criterion {c} is given to both {by_crit[c]!r} and {p.get('interviewer')!r}")
            by_crit.setdefault(c, p.get("interviewer"))
    names = {p.get("interviewer") for p in panel}
    out = {}
    for i, q in enumerate(questions):
        who = q.get("interviewer") or by_crit.get(q.get("criterion"))
        if q.get("interviewer") and q["interviewer"] not in names:
            problems.append(f"question {q.get('id', i + 1)} names interviewer {q['interviewer']!r}, who is not on the panel")
        out[i] = who
    return out, problems


def validate(core, crit_ids, personal_kits=()):
    """-> (errors, warnings) for the panel section of core.json (and routing of personal questions)."""
    panel = core.get("panel")
    errors, warnings = [], []
    if not panel:
        return errors, warnings
    if not isinstance(panel, list):
        return ["core.json: panel must be a list of {interviewer, criteria, minutes}"], warnings
    seen = set()
    for i, p in enumerate(panel, 1):
        name = p.get("interviewer")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"core.json panel #{i}: interviewer missing (a role label like 'Payments lead' is enough)")
        elif name in seen:
            errors.append(f"core.json panel: interviewer {name!r} listed twice")
        seen.add(name)
        for c in p.get("criteria", []) or []:
            if c not in crit_ids:
                errors.append(f"core.json panel {name!r}: unknown criterion {c}")
        if not p.get("criteria"):
            warnings.append(f"core.json panel {name!r}: no criteria assigned")
    qs = core.get("questions", [])
    who, problems = assign(core, qs)
    errors += [f"core.json panel: {p}" for p in problems]
    load = {}
    for i, q in enumerate(qs):
        if not who[i]:
            errors.append(f"core.json: question {q.get('id', i + 1)} ({q.get('criterion')}) has no interviewer on the panel")
        else:
            load[who[i]] = load.get(who[i], 0) + (q.get("minutes") or 0)
    for kit_name, kit in personal_kits:
        kq = kit.get("questions", [])
        kwho, kprob = assign(core, kq)
        errors += [f"{kit_name}: {p}" for p in kprob]
        for i, q in enumerate(kq):
            if not kwho[i]:
                warnings.append(f"{kit_name}: personal question {q.get('id', i + 1)} ({q.get('criterion')}) has no "
                                f"interviewer; it goes to {panel[0].get('interviewer')!r}")
    for p in panel:
        if isinstance(p.get("minutes"), (int, float)) and load.get(p.get("interviewer"), 0) > p["minutes"]:
            errors.append(f"core.json panel {p['interviewer']!r}: core questions take {load[p['interviewer']]} min, "
                          f"slot is {p['minutes']}")
    return errors, warnings


def label(core, q):
    """Interviewer for one question (first panel member as fallback); None when there is no panel."""
    panel = core.get("panel") or []
    if not panel:
        return None
    who, _ = assign(core, [q])
    return who[0] or panel[0].get("interviewer")
