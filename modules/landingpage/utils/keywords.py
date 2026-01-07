import re

def extract_keywords(user_message: str):
    cleaned = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ\s\-]", " ", user_message).strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    tokens = [t for t in parts if len(t) >= 3]

    phrases = []
    if len(parts) >= 2:
        for n in (4, 3, 2):
            if len(parts) >= n:
                phrases.append(" ".join(parts[:n]))
        phrases.append(" ".join(parts[-2:]))
        if len(parts) >= 3:
            phrases.append(" ".join(parts[-3:]))

    out, seen = [], set()
    for x in phrases + tokens:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            out.append(x)

    return out[:12]
