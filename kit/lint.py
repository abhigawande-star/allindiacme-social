"""Mechanical checks for a queue post. lint(post) -> list of violations (empty = clean).

Rebuilt 22 Sep 2026. Covers the checkable parts of standards.md section A. Clinical accuracy,
tone and necessity are the Quality Guardian's judgement, not this file's.
"""
import re

PILLARS = {"clinical", "educational", "brand", "ayush"}
THEMES = {"navy", "ivory", "gold"}
EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF‍️]")
ACRONYMS = {"CME", "AYUSH", "BAMS", "BHMS", "NICU", "ICU", "WHO", "ICMR", "IAP", "FOGSI", "RSSDI",
            "ISA", "ISCCM", "NNF", "NMC", "OPD", "HbA1c", "ECG", "COPD", "IV", "India", "Indian",
            "I", "IST", "LLP", "Covelis", "Health", "Tech", "ADA", "ESC", "NICE", "GINA", "GOLD",
            "KDIGO", "AHA", "ACOG", "RCOG", "SGLT2", "GLP-1", "DKA", "PPH", "BP", "CPR", "BLS", "ALS"}
BANNED = [
    (r"\baccredit", "accreditation claim"),
    (r"\b\d+(\.\d+)?\s*(cme\s*)?credits?\b", "credit figure"),
    (r"₹|\bINR\b|\bRs\.?\s*\d", "price"),
    (r"\bfree\b", "price claim ('free')"),
    (r"\bDr\.?\s+[A-Z]", "named doctor"),
    (r"\b(AIIMS|PGIMER|JIPMER|CMC Vellore)\b", "named institution"),
    (r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
     "session date"),
    (r"masterclasses?\s*(,|and)\s*(cross-specialty\s+)?CME", "masterclass set against CME (rule A2)"),
]


def _sentence_case_problem(s):
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-']*", s)
    caps = [w for i, w in enumerate(words) if i > 0 and w[0].isupper() and w not in ACRONYMS
            and not re.search(r"[.!?:]\s+" + re.escape(w), s)]
    return len(words) > 3 and len(caps) >= 2


def lint(post):
    v = []
    for k in ("id", "date", "slot", "pillar", "theme", "eyebrow", "headline", "sub", "caption", "status"):
        if not post.get(k):
            v.append("missing field: " + k)
    if v:
        return v
    if post["pillar"] not in PILLARS:
        v.append("pillar must be one of " + ", ".join(sorted(PILLARS)))
    if post["theme"] not in THEMES:
        v.append("theme must be navy, ivory or gold")
    if post["slot"] not in ("09:30", "17:30"):
        v.append("slot must be 09:30 or 17:30")
    if post["pillar"] == "clinical" and not (post.get("source") and post.get("source_url")):
        v.append("clinical post needs source and source_url")

    visible = " ".join([post["eyebrow"], post["headline"], post["sub"], post["caption"]])
    if EMOJI.search(visible):
        v.append("emoji present")
    for field in ("eyebrow", "headline", "sub"):
        if _sentence_case_problem(post[field]):
            v.append(field + " looks like Title Case; use sentence case")
    for pat, why in BANNED:
        if re.search(pat, visible, re.I if why != "named doctor" else 0):
            v.append("banned content: " + why)
    # rule A2: masterclass only ever as the format of CME
    sents = [s for fld in ("eyebrow", "headline", "sub", "caption")
             for s in re.split(r"(?<=[.!?])\s+|\n+", post[fld])]
    for sent in sents:
        if re.search(r"masterclass", sent, re.I) and "CME" not in sent:
            v.append("rule A2: 'masterclass' used without CME in the same sentence: " + sent[:80])

    cap = post["caption"]
    body, sep, tags = cap.rpartition("\n\n")
    if not sep or not re.fullmatch(r"#CME #MedEd #[A-Za-z0-9]+", tags.strip()) or tags != tags.strip():
        v.append("caption must end with a blank line then exactly '#CME #MedEd #Theme'")
    if "#" in body:
        v.append("hashtag inside caption body")
    n = len(body.split())
    if not 60 <= n <= 180:
        v.append("caption body is %d words; must be 60-180" % n)
    if len(post["headline"]) > 90:
        v.append("headline over 90 characters")
    if len(post["sub"]) > 200:
        v.append("support line over 200 characters")
    if len(post["eyebrow"]) > 28:
        v.append("eyebrow over 28 characters")
    if re.search(r"\b\d+(\.\d+)?\s*%", visible) and post["pillar"] != "clinical":
        v.append("statistic in a non-clinical post; numbers need a source")
    return v
