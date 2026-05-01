import re

_STOPWORDS = {
    "siapa",
    "apa",
    "apakah",
    "kapan",
    "dimana",
    "di mana",
    "mengapa",
    "kenapa",
    "bagaimana",
    "berapa",
    "jelaskan",
    "tolong",
    "sebutkan",
    "caranya",
    "cara",
    "yang",
    "itu",
    "ini",
    "adalah",
}

def extract_keywords(user_message: str):
    cleaned = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ\s\-]", " ", user_message).strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    tokens = [t for t in parts if len(t) >= 3]
    vitamins = re.findall(r"\bvitamin\s+([a-z])\b", cleaned.lower())

    phrases = []
    if len(parts) >= 2:
        for n in (4, 3, 2):
            if len(parts) >= n:
                phrases.append(" ".join(parts[:n]))
        phrases.append(" ".join(parts[-2:]))
        if len(parts) >= 3:
            phrases.append(" ".join(parts[-3:]))
    for v in vitamins:
        phrases.append(f"vitamin {v}")

    out, seen = [], set()
    for x in phrases + tokens:
        k = x.lower()
        if k in _STOPWORDS:
            continue
        if k not in seen:
            seen.add(k)
            out.append(x)

    return out[:12]
