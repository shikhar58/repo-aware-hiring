"""Shared helpers for repo-aware-hiring scripts. Standard library only."""
import json
import re
import subprocess
import zipfile
from pathlib import Path

LEVELS = {0, 1, 2, 3}
STATUSES = {"evidenced", "weak", "no_evidence", "contradicted"}
CONFIDENCES = {"high", "medium", "low"}
CV_SUFFIXES = {".md", ".txt", ".pdf", ".docx"}

# ---------------------------------------------------------------- loading

def load_json(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cv_files(role_dir):
    folder = Path(role_dir) / "cvs"
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in CV_SUFFIXES)


def extract_text(path):
    """Return plain text for md/txt/pdf/docx. Raises RuntimeError if unreadable."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                                 capture_output=True, text=True, timeout=60)
        except FileNotFoundError as e:
            raise RuntimeError("pdftotext not installed (poppler-utils)") from e
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip() or "pdftotext failed")
        return out.stdout
    if suffix == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", "\t", xml)
        text = re.sub(r"<[^>]+>", "", xml)
        return (text.replace("&amp;", "&").replace("&lt;", "<")
                    .replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'"))
    raise RuntimeError(f"unsupported file type {suffix}")

# ---------------------------------------------------------------- PII patterns

CODE_HOSTS = ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org")

# Field labels in English, French, German, Spanish, Italian, Dutch and Portuguese. Other languages
# rely on the agent's review step; check_redaction.py cannot verify them.
_DOB = (r"date of birth|d\.?o\.?b\.?|born(?: on| in)?|n[ée]e? le|date de naissance|geburtsdatum|geboren(?: am)?|"
        r"fecha de nacimiento|nacid[oa] el|data di nascita|nat[oa] il|geboortedatum|geboren op|data de nascimento|nascid[oa] em")
_AGE_LABEL = r"age[d]?|[âa]ge|alter|edad|et[àa]|leeftijd|idade"
_AGE_UNIT = r"years?|yrs?|ans|jahre|años|anos|anni|jaar"
_FIELDS = (r"nationality|citizenship|visa status|marital status|gender|sex|religion|"
           r"nationalit[ée]|citoyennet[ée]|[ée]tat civil|situation (?:de )?famil(?:le|iale)|sexe|"
           r"staatsangeh[öo]rigkeit|nationalit[äa]t|familienstand|geschlecht|konfession|religion|"
           r"nacionalidad|ciudadan[íi]a|estado civil|sexo|religi[óo]n|"
           r"nazionalit[àa]|cittadinanza|stato civile|sesso|religione|"
           r"nationaliteit|burgerlijke staat|geslacht|religie|"
           r"nacionalidade|religi[ãa]o")

PII_PATTERNS = {
    "email": re.compile(r"[\w.+\-\[\]]+@[\w-]+\.[\w.-]+"),
    # Code-host links are kept for the human reviewer (prep_report.json) but removed from
    # the text the model scores: usernames identify people and the scorer must not fetch them.
    "code_link": re.compile(r"(?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org|codeberg\.org)/[\w./-]+", re.I),
    "web_link": re.compile(r"https?://\S+", re.I),
    "social_link": re.compile(r"(?:https?://)?(?:www\.)?(?:linkedin|twitter|x|facebook|instagram|xing)\.com/\S+", re.I),
    "phone": re.compile(r"(?<![\w/])\+?\(?\d[\d\s().-]{6,}\d(?![\w/])"),
    "date_of_birth": re.compile(rf"(?<!\w)(?:{_DOB})(?!\w)[^\n]*", re.I),
    "age": re.compile(rf"(?<!\w)(?:(?:{_AGE_LABEL})\s*:?\s*\d{{2}}|\d{{2}}\s*(?:{_AGE_UNIT})(?:[\s-](?:old|alt))?)(?!\w)", re.I),
    "personal_field": re.compile(rf"(?<!\w)(?:{_FIELDS})\s*:[^\n]*", re.I),
    "photo": re.compile(r"!\[[^\]]*\]\([^)]*\)|(?<!\w)(?:photo(?:graph)?|foto|bild)\s*:[^\n]*", re.I),
}

SOFT_PATTERNS = {
    "gendered_word": re.compile(r"\b(?:he|she|him|her|his|hers|himself|herself|mother|father|wife|husband)\b", re.I),
    # Titles only when followed by a capitalised word, so "900 ms" is not a hit.
    "title": re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Mx|Mme|Mlle|Herr|Frau|Sr|Sra|Dhr|Mevr)\.?\s+[A-Z]"),
    "family_status": re.compile(r"\b(?:married|divorced|widowed|maternity|paternity|mari[ée]e?|verheiratet|casad[oa]|sposat[oa]|getrouwd)\b", re.I),
}

YEAR_RANGE = re.compile(r"^(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}$")
THOUSANDS = re.compile(r"^\d{1,3}(?:[ ,. ]\d{3})+$")
# 01.2019 - 05.2023, 2019.01 - 2023.05, 1.1.1990 (dates of birth are caught by their label instead)
DATE_LIKE = re.compile(r"^(?:\d{1,2}[./-])?(?:\d{1,2}[./-])?(?:19|20)\d{2}(?:\s*[-–]\s*(?:\d{1,2}[./-])?(?:\d{1,2}[./-])?(?:19|20)\d{2})?$"
                       r"|^(?:19|20)\d{2}[./-]\d{1,2}(?:\s*[-–]\s*(?:19|20)\d{2}[./-]\d{1,2})?$")
CONTACT_WORDS = re.compile(r"\b(?:phone|tel|t[ée]l[ée]phone|telefon|tel[ée]fono|telefone|telefoon|mobile?|cell|portable|"
                           r"handy|m[óo]vil|cellulare|whatsapp|contact|kontakt|contacto|contatto)\b", re.I)


def phone_like(match_text, line=""):
    """Is this digit run a phone number? Uses the surrounding line, because "12 000 000 users"
    and "612 345 678" look the same out of context."""
    t = match_text.strip()
    digits = re.sub(r"\D", "", t)
    if not 8 <= len(digits) <= 15 or YEAR_RANGE.match(t.strip("() ")) or DATE_LIKE.match(t.strip("() ")):
        return False
    if t.startswith("+") or re.match(r"^\(\+?\d{1,5}\)", t):   # +34 ..., (030) ...
        return True
    rest = line.replace(match_text, " ")
    contact = (bool(CONTACT_WORDS.search(line)) or "@" in line or bool(re.search(r"[·|•]", line))
               or not re.search(r"[A-Za-zÀ-ÿ]{3,}", rest))  # the number is the whole line
    if contact:
        return True
    if THOUSANDS.match(t):
        return False                       # 12 000 000 users, 1,000,000,000 rows
    return bool(re.search(r"[\s().-]", t))  # grouped digits in prose; bare IDs are kept


CV_HEADER_WORDS = {"curriculum", "vitae", "cv", "resume", "résumé", "lebenslauf", "profile", "profil",
                   "contact", "personal", "details", "information", "about", "me", "summary", "page",
                   # job-title words: a heading like "SENIOR BACKEND ENGINEER" is not a name
                   "engineer", "developer", "programmer", "architect", "scientist", "analyst", "consultant",
                   "designer", "manager", "director", "lead", "senior", "junior", "principal", "staff", "head",
                   "intern", "specialist", "administrator", "backend", "frontend", "full-stack", "fullstack",
                   "software", "data", "devops", "sre", "cto", "ceo", "officer", "ingénieur", "développeur",
                   "entwickler", "ingenieur", "ingeniero", "desarrollador", "sviluppatore", "ontwikkelaar"}
NAME_PARTICLES = {"de", "da", "das", "do", "dos", "di", "del", "della", "van", "von", "der", "den", "le", "la",
                  "al", "el", "bin", "ibn", "ben", "y", "e", "du", "ter", "ten", "zu", "mac", "st"}
_NAME_WORD = re.compile(r"[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*")


def _clean_line(line):
    line = re.sub(r"^[#*>\s]+|[*\s]+$", "", line).strip()
    line = re.sub(r"^(?:name|nom|nombre|nome|naam)\s*:\s*", "", line, flags=re.I)
    return re.split(r"\s*[,|·•]\s*", line)[0].strip()   # drop ", MSc" or "| Engineer"


def looks_like_name(line):
    words = line.split()
    if not 2 <= len(words) <= 5:
        return False
    if {w.lower().strip(".") for w in words} & CV_HEADER_WORDS:
        return False
    core = [w for w in words if w.lower() not in NAME_PARTICLES]
    return len(core) >= 2 and all(_NAME_WORD.fullmatch(w) for w in core)


def probable_name(original_text, max_lines=10):
    """Best guess at the candidate's name from the top of the CV, skipping headings such as
    "Curriculum Vitae". Only a guess: identities.json must be confirmed by the agent."""
    seen = 0
    for raw in original_text.splitlines():
        if not raw.strip():
            continue
        seen += 1
        if seen > max_lines:
            break
        line = _clean_line(raw)
        if looks_like_name(line):
            return line
    return None


# Particles that are also everyday words in CV text ("de", "la", "der"); redacting them everywhere
# would wreck the text. Others ("Al", "El", "Bin") are kept as tokens and redacted.
COMMON_WORD_PARTICLES = {"de", "da", "das", "do", "dos", "di", "del", "della", "van", "von", "der", "den",
                         "le", "la", "y", "e", "du", "ter", "ten", "zu", "st"}


def name_tokens(name):
    """Name parts to redact/check. Two-letter parts (e.g. 'Al', 'Li') count; common-word particles do not."""
    return [t for t in re.split(r"[\s'’.-]+", name or "") if len(t) >= 2 and t.lower() not in COMMON_WORD_PARTICLES]


def find_pii(text, names=()):
    """Return list of (kind, snippet). Hard findings only (soft words are separate).
    names: every confirmed name/alias of the candidate."""
    if isinstance(names, str):
        names = [names]
    hits = []
    for line in text.splitlines():
        for kind, pat in PII_PATTERNS.items():
            for m in pat.finditer(line):
                s = m.group(0)
                if kind == "phone" and not phone_like(s, line):
                    continue
                hits.append((kind, s.strip()[:80]))
    for name in names:
        for tok in name_tokens(name):
            if re.search(rf"(?<!\w){re.escape(tok)}(?!\w)", text, re.I):
                hits.append(("name", tok))
    return hits


def find_soft(text):
    return [(k, m.group(0)) for k, p in SOFT_PATTERNS.items() for m in p.finditer(text)]

# ---------------------------------------------------------------- identities
# identities.json (private, deleted when the round closes):
#   {"C01": {"name": "Sarah Johnson", "aliases": ["S. Johnson"], "source": "auto|agent", "confirmed": false}}


def load_identities(role_dir):
    p = Path(role_dir) / "identities.json"
    return load_json(p) if p.exists() else {}


def identity_names(entry):
    if not entry:
        return []
    return [n for n in [entry.get("name")] + list(entry.get("aliases", [])) if n]


# ---------------------------------------------------------------- injection

INJECTION_PATTERNS = [
    # English
    r"ignore (?:all |any )?(?:the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)",
    r"disregard (?:the |all |any )?(?:previous|prior|above|rubric|instructions)",
    r"\b(?:system|developer) prompt\b",
    r"\byou are (?:now |an? )?(?:ai|assistant|language model|llm|chatgpt|claude)\b",
    r"\b(?:ai|llm|language model|assistant|screener|recruit(?:er|ing) (?:bot|system))s?[, ]+(?:must|should|please|note)\b",
    r"\b(?:rank|score|rate|mark)\s+(?:this|the|me|him|her|them)?\s*(?:candidate|applicant|cv|resume)?\s*(?:as\s+)?(?:first|top|highest|#?1|10/10|maximum|3/3)\b",
    r"\b(?:this|the) candidate (?:is|must be) (?:the )?(?:best|ideal|perfect|top)\b",
    r"\bnew instructions?\b",
    r"<\s*/?\s*(?:system|instructions?|prompt)\s*>",
    # French
    r"\bignore[zr]? (?:toutes )?(?:les )?instructions (?:pr[ée]c[ée]dentes|ci-dessus|ant[ée]rieures)",
    r"\bclasse[zr]? (?:ce|cette) candidat(?:e)? (?:en )?premi[eè]re?\b",
    # German
    r"\bignorier(?:e|en sie)? (?:alle )?(?:vorherigen|obigen|bisherigen) (?:anweisungen|instruktionen)",
    r"\b(?:diese[nr]?|den) (?:kandidat(?:en|in)?|bewerber(?:in)?) (?:als )?(?:erste[nr]?|beste[nr]?|top)\b",
    # Spanish / Portuguese / Italian / Dutch
    r"\bignora(?:r)? (?:todas )?(?:las |as |le )?(?:instrucciones|instru[çc][õo]es|istruzioni) (?:anteriores|previas|precedenti)",
    r"\b(?:clasifica|classifica|ordena)(?:r)? (?:a )?(?:este|esta|questo|questa) candidat[oa] (?:como |come )?(?:primer[oa]?|primeir[oa]|prim[oa])\b",
    r"\bnegeer (?:alle )?(?:vorige|eerdere) instructies",
]
INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.I)


def scan_injection(text):
    return [m.group(0) for m in INJECTION_RE.finditer(text)]

# ---------------------------------------------------------------- evidence grounding

STOP = set("""a an the and or of to in on for with at by from as is was were be been are this that
these those it its into over under per via using used use our their your my i we they""".split())


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9+#.]+", text.lower().replace("’", "'")) if t not in STOP and t.strip(".")]


def grounding(evidence, source_text):
    """Fraction of the evidence's content tokens that appear in the source text."""
    ev = [t.strip(".") for t in tokens(evidence)]
    ev = [t for t in ev if t]
    if not ev:
        return 0.0
    src = {t.strip(".") for t in tokens(source_text)}
    return sum(1 for t in ev if t in src) / len(ev)
