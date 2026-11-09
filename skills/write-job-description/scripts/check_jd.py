#!/usr/bin/env python3
"""Check a job description before it is published. Standard library only.

Usage: python3 check_jd.py hiring/<role-slug> [--jd path/to/jd.md]

ERRORS (exit code 1): possible leaks of internal details. A JD is public.
  - file paths, and any path or identifier named in repo-profile.md, brief.md or the codebase map
  - environment-variable names, IP addresses, internal hostnames, credentials
  - statements of security weaknesses or missing safeguards ("no backups", "vulnerable", "breach")
WARNINGS (exit code 0): fairness, structure and consistency.
  - gender-coded, age-coded and exclusionary wording; "native speaker"; years-of-experience demands
  - missing sections, too many must-haves, no pay range, unfilled placeholders, length
  - must-haves that don't match the screening rubric (when rubric.json exists)
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hiring-workspace" / "scripts"))
try:
    import wslib  # noqa: E402
except ImportError:  # the workspace skill is optional for single-repo use
    wslib = None

PUBLIC_TECH = {
    "python", "fastapi", "django", "flask", "postgresql", "postgres", "mysql", "sqlalchemy", "sqlmodel", "alembic",
    "pytest", "docker", "kubernetes", "terraform", "react", "typescript", "javascript", "node.js", "go", "rust",
    "java", "redis", "kafka", "aws", "gcp", "azure", "github", "gitlab", "pgbouncer", "linux", "graphql", "rest",
    "ci", "sql", "orm", "asyncpg", "psycopg", "mypy", "ruff", "sentry",
}
CODE_EXT = r"(?:py|js|jsx|ts|tsx|go|rs|java|kt|rb|php|cs|sh|bash|ya?ml|json|toml|sql|tf|ini|cfg|conf|env|lock|mako|proto)"
PATH_RE = re.compile(rf"(?<![\w/@.])(?:[\w.-]+/)+[\w.-]+(?:\.{CODE_EXT})?\b|(?<![\w/@])[\w-]+\.{CODE_EXT}\b")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]{2,}\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HOST_RE = re.compile(r"\b[\w-]+(?:\.[\w-]+)*\.(?:internal|local|corp|lan|intra)\b|\blocalhost\b|\bstaging\.[\w.-]+", re.I)
CRED_RE = re.compile(r"\b(?:password|passwd|api[ _-]?key|secret[ _-]?key|private key|access token|bearer)\b\s*[:=]", re.I)
WEAKNESS_RE = re.compile(
    r"\bvulnerab\w*|\bbreach(?:es|ed)?\b|\bunpatched\b|\bexploit(?:s|ed|able)?\b|\binsecure\b|"
    r"\b(?:no|without|lack(?:s|ing)? (?:any )?)\s*(?:backups?|replication|monitoring|tests?|test coverage|encryption|"
    r"access control|authentication)\b|\b(?:currently|right now) (?:broken|failing|down)\b", re.I)

INCLUSIVE = [
    (re.compile(r"\b(?:he|him|his|she|her|hers)\b", re.I), "gendered pronoun: use “you” or “they”"),
    (re.compile(r"\b(?:guys|manpower|man-hours|chairman|salesman|brotherhood)\b", re.I), "gendered term"),
    (re.compile(r"\b(?:rock\s?stars?|ninjas?|gurus?|wizards?|superheroes|superhero|unicorns?|crush(?:ing)? it|killer)\b", re.I),
     "hype word: tends to put off qualified applicants, often women"),
    (re.compile(r"\b(?:dominant|dominate|aggressive(?:ly)?|fearless|competitive(?! (?:salary|pay|compensation|package|benefits)))\b", re.I),
     "masculine-coded word"),
    (re.compile(r"\b(?:young|youthful|digital natives?|recent grad(?:uate)?s?|fresh grad(?:uate)?s?|energetic)\b", re.I),
     "age-coded wording"),
    (re.compile(r"\bnative (?:\w+ )?speakers?\b", re.I), "“native speaker” excludes fluent non-natives: state the level needed (e.g. C1)"),
    (re.compile(r"\b(?:culture fit|works? hard,? (?:and )?plays? hard|like a family|we'?re a family|fast[- ]paced|wear many hats)\b", re.I),
     "vague or exclusionary phrase"),
    (re.compile(r"\b\d+\s*\+?\s*(?:years|yrs)\b(?: of)?", re.I), "years-of-experience requirement: describe the capability instead"),
    (re.compile(r"\b(?:bachelor'?s?|master'?s?|ph\.?d|degree)\b[^.\n]{0,40}\b(?:required|must|mandatory)\b|\b(?:required|must have)\b[^.\n]{0,40}\bdegree\b", re.I),
     "degree requirement: only keep if the job truly needs it"),
]

SECTIONS = {
    "about": r"about the role",
    "work": r"what you'?ll (?:work on|do)",
    "must": r"must[- ]haves?|requirements|what you(?:'ll)? need",
    "nice": r"nice[- ]to[- ]haves?|bonus",
    "hire": r"how we hire|hiring process|interview process",
    "offer": r"what we offer|benefits|why join",
}
STOP = set("""a an the and or of to in on for with at by from as is are be been was were this that these those it its into
over under per via using use our your you we they their has have had can will would should may might not no do does
on-call own owned owning safely safe real production data""".split())
CURRENCY_RE = re.compile(r"[€$£₹¥]|\b(?:EUR|USD|GBP|INR|CHF|SEK|NOK|DKK|PLN|CAD|AUD)\b|\b\d{2,3}\s?[kK]\b")


def sections(text):
    out, cur = {}, None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^#{2,3}\s+(.+?)\s*$", line)
        if m:
            cur = None
            for key, pat in SECTIONS.items():
                if re.search(pat, m.group(1), re.I):
                    cur = key
                    out.setdefault(key, [])
                    break
            continue
        if cur and line.strip():
            out[cur].append((i, line.strip()))
    return out


def bullets(lines):
    return [(i, re.sub(r"^[-*•]\s+|^\d+\.\s+", "", ln)) for i, ln in lines if re.match(r"^(?:[-*•]|\d+\.)\s+", ln)]


def tokens(text):
    return {t for t in re.findall(r"[a-z][a-z0-9+#.-]*", text.lower()) if t not in STOP and len(t) > 2}


def internal_terms(role):
    """Paths and identifiers the profile and brief mention: none of these may appear in the JD."""
    terms = set()
    sources = [role / "repo-profile.md", role / "brief.md", role / "focus.md", role.parent / "_repo" / "codebase-map.md"]
    ws = wslib.find_workspace(role) if wslib else None
    if ws:
        data = wslib.load(ws)
        sources.append(ws / "system" / "system-map.md")
        for r in wslib.active_repos(data):
            sources.append(wslib.map_file(ws, r))
            names = {r["name"]}
            inv = wslib.map_dir(ws, r["name"]) / "inventory.json"
            if inv.exists():
                names |= set(json.loads(inv.read_text()).get("links", {}).get("published", {}).values())
            # only distinctive names: 'checkout-svc' or 'acme_payments' leak, a plain word like 'billing' doesn't
            terms |= {n for n in names if re.search(r"[-_\d/@]", n) and n.lower() not in PUBLIC_TECH}
    for p in sources:
        name = p.name
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        for m in PATH_RE.finditer(t):
            s = m.group(0).strip(".,;:)")
            if "/" in s or "." in s:
                terms.add(s)
                base = s.rsplit("/", 1)[-1]
                if "." in base and len(base) > 4:
                    terms.add(base)
        for m in re.finditer(r"`([^`\n]{3,60})`", t):
            s = m.group(1).strip()
            if s.lower() in PUBLIC_TECH or " " in s and not re.search(r"[/_.]", s):
                continue
            if re.search(r"[/_]|\.\w", s) or re.fullmatch(r"[a-z]+[A-Z]\w+", s):
                terms.add(s)
    return {t for t in terms if t.lower() not in PUBLIC_TECH and len(t) >= 4}


def find_leaks(text, role):
    """Possible leaks of internal details in public-facing text (a job posting, or interview questions a
    candidate will hear). Returns [(line_no, message)]. Shared with the interview-kit validator."""
    lines = text.splitlines()
    errors = []

    def where(pos_text, needle):
        for i, ln in enumerate(lines, 1):
            if needle in ln:
                return i
        return "?"

    for i, ln in enumerate(lines, 1):
        for m in PATH_RE.finditer(ln):
            s = m.group(0).strip(".,;:)")
            if s.lower() in PUBLIC_TECH or re.fullmatch(r"node\.js|vue\.js|next\.js|\w+\.io", s, re.I):
                continue
            if "/" in s and re.fullmatch(r"[A-Za-z]+/[A-Za-z]+", s):  # "CI/CD", "TCP/IP"
                continue
            errors.append((i, f"looks like a file path: {s!r}"))
        for m in ENV_RE.finditer(ln):
            errors.append((i, f"looks like an internal environment variable: {m.group(0)!r}"))
        for rx, what in ((IP_RE, "IP address"), (HOST_RE, "internal hostname"), (CRED_RE, "credential")):
            for m in rx.finditer(ln):
                errors.append((i, f"{what}: {m.group(0)!r}"))
        for m in WEAKNESS_RE.finditer(ln):
            errors.append((i, f"describes a security weakness or missing safeguard: {m.group(0)!r} (say what the hire will build instead)"))
    flagged = {(i, msg.split(": ", 1)[-1].strip("'\"")) for i, msg in errors}
    for term in sorted(internal_terms(role)):
        if re.search(rf"(?<![\w/]){re.escape(term)}(?![\w/])", text):
            line_no = where(text, term)
            if any(ln == line_no and term in f for ln, f in flagged):
                continue  # already reported as a path on this line
            errors.append((line_no, f"names an internal detail (from the codebase maps, repo profile or brief): {term!r}"))

    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role_dir")
    ap.add_argument("--jd", default=None, help="default: <role_dir>/jd.md")
    args = ap.parse_args(argv)
    role = Path(args.role_dir)
    jd_path = Path(args.jd) if args.jd else role / "jd.md"
    if not jd_path.exists():
        print(f"No job description at {jd_path}")
        return 2
    text = jd_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors, warnings, notes = [], [], []

    def where(pos_text, needle):
        for i, ln in enumerate(lines, 1):
            if needle in ln:
                return i
        return "?"

    errors.extend(find_leaks(text, role))

    # ---------------- inclusive language (warnings)
    for i, ln in enumerate(lines, 1):
        for rx, why in INCLUSIVE:
            for m in rx.finditer(ln):
                warnings.append((i, f"{why}: {m.group(0)!r}"))

    # ---------------- structure (warnings)
    secs = sections(text)
    missing = [k for k in ("about", "work", "must", "nice", "hire") if k not in secs]
    names = {"about": "About the role", "work": "What you'll work on", "must": "Must-haves",
             "nice": "Nice-to-haves", "hire": "How we hire"}
    if missing:
        warnings.append(("-", "missing sections: " + ", ".join(names[k] for k in missing)))
    ai = r"(?:\bAI\b|artificial intelligence|automated)"
    act = r"(?:screen|review|assess|evaluat|rank|shortlist|applica|CVs?\b|r[ée]sum[ée]|decision)"
    if not re.search(rf"{ai}[^.\n\]]{{0,80}}{act}|{act}\w*[^.\n\]]{{0,80}}{ai}", text, re.I):
        warnings.append(("-", "no notice that AI is used in screening: candidates must be told when AI helps decide "
                              "about them (Anthropic's Usage Policy from 12 Nov 2026, and the law in some places). Say "
                              "so in How we hire, or keep the [insert: …] placeholder"))
    for i, ln in enumerate(lines, 1):
        if re.match(r"^#{2,3}\s+.*\b(?:(?:our|the|tech(?:nology)?)\s+stack|technologies(?:\s+we\s+use)?|tools\s+we\s+use|"
                    r"what\s+we\s+(?:use|build\s+with))\b", ln, re.I):
            warnings.append((i, "stack section publishes your exact stack: hint the technologies inside What you'll work on, "
                                "Must-haves and Nice-to-haves instead (keep it only if the hiring manager decided to publish it)"))
    musts = bullets(secs.get("must", []))
    if musts and len(musts) > 5:
        warnings.append((musts[0][0], f"{len(musts)} must-haves: keep to 3–5; long lists deter qualified applicants"))
    flagged = {ln for ln, _ in warnings if isinstance(ln, int)}
    for ln, item in musts:
        if ln in flagged:
            continue
        if re.search(r"\b(?:bachelor'?s?|master'?s?|ph\.?d|degree|diploma)\b", item, re.I):
            warnings.append((ln, f"degree as a must-have: describe the knowledge needed instead, or move it to "
                                 f"nice-to-haves: {item.strip()[:60]!r}"))
        if re.search(r"\b(?:top|elite|leading|prestigious|tier[- ]?(?:1|one)|good|ivy league|russell group)\b[^.\n]{0,20}"
                     r"\b(?:universit\w*|college|school|institute)s?\b|\bIITs?\b|\boxbridge\b", item, re.I):
            warnings.append((ln, f"school pedigree screens out capable people without predicting the work: "
                                 f"{item.strip()[:60]!r}"))
    head = "\n".join(lines[:6])
    pay_placeholder = re.search(r"\[(?:insert:\s*)?(?:salary|pay)[^\]]*\]", head, re.I)
    if not pay_placeholder and (not CURRENCY_RE.search(head) or re.search(r"on request|competitive", head, re.I)):
        warnings.append((2, "no pay range near the top: required in some jurisdictions and increases applications"))
    visible = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # the draft note in a comment isn't a placeholder
    placeholders = sorted(set(re.findall(r"\[[^\]\n]{2,300}\]", visible)))
    placeholders = [p for p in placeholders if not re.match(r"\[[^\]]+\]\(", p)]
    if placeholders:
        notes.append("placeholders to fill before posting: " + ", ".join(placeholders))
    words = len(re.findall(r"\w+", text))
    if words > 900:
        warnings.append(("-", f"{words} words: postings over ~700 words are read less; trim"))

    # ---------------- consistency with the screening rubric (warnings)
    rub_path = role / "rubric.json"
    if rub_path.exists() and musts:
        rubric = json.loads(rub_path.read_text(encoding="utf-8"))
        rmust = [c for c in rubric.get("criteria", []) if c.get("tier") == "must_have"]

        def match(a, b):
            ta, tb = tokens(a), tokens(b)
            return len(ta & tb) >= 2 or (ta and len(ta & tb) / len(ta) >= 0.4)
        for c in rmust:
            text_c = c["name"] + " " + " ".join(c.get("transferable_from", []))
            if not any(match(text_c, b) or match(c["name"], b) for _, b in musts):
                warnings.append(("-", f"rubric must-have not in the JD's Must-haves: {c['name']!r}"))
        for i, b in musts:
            if not any(match(b, c["name"]) for c in rmust):
                warnings.append((i, f"JD must-have is not a rubric must-have (screening won't gate on it): {b[:70]!r}"))
    elif not rub_path.exists():
        notes.append("no rubric.json yet: the Must-haves above will seed it (hiring-rubric)")

    # ---------------- report
    print(f"Checked {jd_path} ({words} words, {len(musts)} must-haves)\n")
    for label, items in (("ERROR", errors), ("warn ", warnings)):
        for line_no, msg in items:
            print(f"{label} line {line_no}: {msg}")
    for n in notes:
        print(f"note  {n}")
    print(f"\n{len(errors)} errors, {len(warnings)} warnings.")
    if errors:
        print("Fix every error before publishing: a job description is public.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
