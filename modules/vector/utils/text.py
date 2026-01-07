import re

def split_to_sentences(text: str):
    parts = []
    for chunk in text.replace("\r", "\n").split("\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        for seg in re.split(r"(?<=[.?!])\s+", chunk):
            s = seg.strip()
            if s:
                parts.append(s)
    return parts


def guess_source_type(filename_lower: str) -> str:
    if filename_lower.endswith(".pdf"):
        return "pdf"
    if filename_lower.endswith(".docx"):
        return "docx"
    if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        return "excel"
    return "unknown"
