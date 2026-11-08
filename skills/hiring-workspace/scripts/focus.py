#!/usr/bin/env python3
"""The focus prompt for a role: free text that tells every step what to concentrate on.

Usage:
  focus.py check   <role_dir>     guard the text, record a new version if it changed, print the version
  focus.py show    <role_dir>     print the current focus text and version
  focus.py history <role_dir>     list earlier versions
  focus.py stale   <role_dir>     list role artifacts written with an older focus version

The focus lives in <role_dir>/focus.md (hiring/<role>/focus.md in single-repo mode, roles/<role>/focus.md in a
workspace). It describes the WORK ("focus on the payment library and how checkout and billing use it"). It can't
add criteria about people (age, gender, nationality, ethnicity, religion, family, health, schools and pedigree,
photos) and can't switch off safeguards (redaction, evidence checks, the rubric). Both are rejected here, and
check_ready.py refuses to continue until the text is fixed.
Every artifact records the version it was written with ("Focus: <version>" in Markdown, "focus_version" in JSON),
so a changed focus shows which artifacts to redo.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wslib  # noqa: E402

PEOPLE = [
    (r"\byoung(?:er)?\b|\byouthful\b|\bdigital natives?\b|\b(?:under|over)\s+\d{2}\b(?!\s*(?:ms|%|k\b|rps|req))|"
     r"\b\d{2}\s*(?:-|to)\s*\d{2}\s+years?\s+old\b|\byears\s+old\b|\baged?\s+\d{2}\b|\b(?:recent|fresh)\s+grad(?:uate)?s?\b|"
     r"\bgraduated\s+(?:after|before|since)\s+\d{4}\b|\bnot\s+too\s+(?:old|senior\s+in\s+age)\b", "age"),
    (r"\b(?:male|female|men|women|woman|girls?|gentlem[ae]n|ladies|lady)\b|\bgender\b|\bhe\s+or\s+she\b|"
     r"\bpregnan\w*\b|\bmaternity\b|\bpaternity\b", "gender or sex"),
    (r"\bnationality\b|\bcitizens?(?:hip)?\s+(?:only|of|required)\b|\bnative\s+(?:\w+\s+)?speakers?\b|\bethnic\w*\b|"
     r"(?<!-)\brace\b(?!\s+conditions?)|\bracial\b|\bcaste\b|\bskin\s+colou?r\b|\bvisa\s+status\b|\bimmigra\w+\b", "origin, race or nationality"),
    (r"\breligio\w+\b|\bchurch\b|\bmosque\b|\btemple\b(?!\s*(?:os|run|\.io))|\bhalal\b|\bkosher\b", "religion"),
    (r"\bmarried\b|\bmarital\b|\bunmarried\b|\bkids\b|\bhas\s+children\b|\bhave\s+children\b|\bchildcare\b|"
     r"\bfamily\s+(?:plans|status|commitments)\b", "family"),
    (r"\bdisab\w+\b|\bable[- ]bodied\b|\bhandicap\w*\b|\bmental\s+health\b|\bmedical\s+(?:history|condition)\b", "disability or health"),
    (r"\btop[- ](?:\d+\s+)?(?:tier\s+)?(?:universit\w+|schools?|colleges?|institutes?)\b|\bivy\s+league\b|\boxbridge\b|"
     r"\bIITs?\b|\bNITs?\b|\belite\s+(?:universit\w+|schools?|colleges?)\b|\bprestigious\b|\btier[- ]?(?:1|one)\s+(?:colleges?|universit\w+|schools?)\b|"
     r"\brussell\s+group\b|\bgood\s+(?:universit\w+|schools?|colleges?)\b|\bwhich\s+(?:universit\w+|school|college)\b", "school pedigree"),
    (r"\bphotos?\b|\bpictures?\s+of\s+(?:the\s+)?candidates?\b|\bgood[- ]looking\b|\battractive\b|\bappearance\b", "appearance"),
    (r"\bpolitic\w+\b|\bunion\s+member\w*\b|\bsexual\w*\b|\bgay\b|\blesbian\b|\btransgender\b|\bLGBT\w*\b", "beliefs or orientation"),
]
SOFT = [
    (r"\bculture\s+fit\b", "'culture fit' tends to favour people like the current team; describe the behaviour you need"),
    (r"\bFAANG\b|\bbig\s+tech\b|\bonly\s+(?:from|ex-)\s*\w+", "employer pedigree is a weak signal; describe the experience instead"),
    (r"\b\d+\+?\s+years?\b", "years of experience screen out capable people; describe what they must be able to do"),
    (r"(?<!react )\bnative\b(?!\s+(?:\w+\s+)?speakers?\b)(?!\s+(?:code|apps?|modules?|bindings?|libraries|extensions?|images?|"
     r"compilation|build|mobile|ui|sdk|android|ios))",
     "check that 'native' refers to technology (React Native, native code), not to people"),
]
OVERRIDE = (r"\bignore\s+(?:the\s+)?(?:rubric|redaction|evidence|rules|guardrails|safeguards|instructions|checks?|gates?)\b|"
            r"\b(?:skip|disable|turn\s+off|bypass|don'?t\s+do|do\s+not\s+do|no)\s+(?:the\s+)?(?:redact\w*|anonymi[sz]\w*|"
            r"evidence\s+checks?|checks?|gates?|validation)\b|\bdon'?t\s+(?:redact|anonymi[sz]e|check)\b|"
            r"\b(?:show|reveal|use|keep)\s+(?:the\s+)?(?:real\s+)?(?:names|identities|photos)\b|"
            r"\brank\s+(?:by|on)\s+(?:school|universit\w+|age|gender|name|nationality|photo)\b|"
            r"\bprefer\s+candidates\s+(?:from|who\s+are)\b|\bwithout\s+(?:evidence|quotes|redaction)\b")
ARTIFACTS = ("brief.md", "repo-profile.md", "jd.md", "rubric.json", "report.md", "interviews/core.json")
MAX_CHARS = 2000


def read_focus(role_dir):
    p = Path(role_dir) / "focus.md"
    if not p.exists():
        return ""
    t = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S)
    t = re.sub(r"^#\s+Focus.*$", "", t, flags=re.M | re.I)
    return "\n".join(ln.rstrip() for ln in t.strip().splitlines()).strip()


def version(text):
    return hashlib.sha256(" ".join(text.split()).lower().encode()).hexdigest()[:12] if text else "none"


def guard(text):
    errors, warnings = [], []
    for pat, label in PEOPLE:
        for m in re.finditer(pat, text, re.I):
            errors.append(f"criterion about people ({label}): \"{m.group(0)}\". The focus describes the work, never the person.")
    for m in re.finditer(OVERRIDE, text, re.I):
        errors.append(f"tries to switch off a safeguard or rank on something other than the work: \"{m.group(0)}\". Redaction, evidence checks and the rubric "
                      "always apply.")
    for pat, msg in SOFT:
        for m in re.finditer(pat, text, re.I):
            warnings.append(f"\"{m.group(0)}\": {msg}")
    if len(text) > MAX_CHARS:
        warnings.append(f"the focus is {len(text)} characters; keep it under {MAX_CHARS} so every step can apply all of it")
    return errors, warnings


def history_path(role_dir):
    return Path(role_dir) / "focus-history.json"


def record(role_dir, text):
    v = version(text)
    hp = history_path(role_dir)
    hist = json.loads(hp.read_text()) if hp.exists() else []
    if not hist or hist[-1]["version"] != v:
        hist.append({"version": v, "saved_at": wslib.now(), "text": text})
        hp.write_text(json.dumps(hist, indent=2) + "\n", encoding="utf-8")
    return v


def artifact_version(path):
    try:
        t = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if path.suffix == ".json":
        try:
            return json.loads(t).get("focus_version")
        except (ValueError, AttributeError):
            return None
    m = re.search(r"Focus:\s*`?([0-9a-f]{12}|none)", t[:3000])
    return m.group(1) if m else None


def stale(role_dir, current):
    out = []
    for name in ARTIFACTS:
        p = Path(role_dir) / name
        if not p.exists():
            continue
        v = artifact_version(p)
        if v is None:
            if current != "none":
                out.append((name, "no focus version recorded (written before the focus existed?)"))
        elif v != current:
            out.append((name, f"written with focus {v}, current is {current}"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("check", "show", "history", "stale"))
    ap.add_argument("role_dir")
    a = ap.parse_args(argv)
    rd = Path(a.role_dir)
    text = read_focus(rd)
    v = version(text)
    if a.cmd == "show":
        print(f"Focus {v}\n\n{text or '(no focus set: every step uses the brief and the maps only)'}")
        return 0
    if a.cmd == "history":
        hp = history_path(rd)
        for h in (json.loads(hp.read_text()) if hp.exists() else []):
            print(f"{h['version']}  {h['saved_at']}  {h['text'][:90]!r}")
        return 0
    if a.cmd == "stale":
        s = stale(rd, v)
        for name, why in s:
            print(f"  stale: {name}: {why}")
        print(f"{len(s)} artifact(s) to redo for focus {v}." if s else f"All artifacts match focus {v}.")
        return 1 if s else 0
    errors, warnings = guard(text)
    for e in errors:
        print(f"  error: {e}")
    for w in warnings:
        print(f"  warn:  {w}")
    if errors:
        print(f"FAIL focus ({rd / 'focus.md'}): fix the text above; nothing was recorded.")
        return 1
    if rd.exists():
        record(rd, text) if text else None
    print(f"OK   focus {v}" + ("" if text else " (no focus set)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
