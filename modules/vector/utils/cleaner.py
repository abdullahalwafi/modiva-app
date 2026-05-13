import re

from django.conf import settings

from modules.landingpage.utils.gemini import clean_text_with_gemini


def _normalize_whitespace(text: str) -> str:
    text = str(text).replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_numeric_tokens(text: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)?%?", str(text))


def _looks_too_different(raw_text: str, cleaned_text: str) -> bool:
    raw = _normalize_whitespace(raw_text)
    cleaned = _normalize_whitespace(cleaned_text)

    if not raw or not cleaned:
        return True

    raw_nums = _extract_numeric_tokens(raw)
    cleaned_nums = _extract_numeric_tokens(cleaned)
    if raw_nums != cleaned_nums:
        return True

    raw_len = len(raw)
    cleaned_len = len(cleaned)
    ratio = cleaned_len / max(raw_len, 1)
    if ratio < 0.55 or ratio > 1.35:
        return True

    return False


def clean_row_text(row_text: str) -> tuple[str, str]:
    raw_text = _normalize_whitespace(row_text)
    if not raw_text:
        return "", "raw_empty"

    web_mode = getattr(settings, "WEB_MODE", "production")
    if web_mode != "production":
        return raw_text, "developer_raw"

    try:
        cleaned_text = clean_text_with_gemini(raw_text)
    except Exception:
        return raw_text, "cleaner_error_local"

    cleaned_text = _normalize_whitespace(cleaned_text)
    if not cleaned_text:
        return raw_text, "cleaner_empty_local"

    if _looks_too_different(raw_text, cleaned_text):
        return raw_text, "cleaner_rejected_local"

    return cleaned_text, "cleaner_ai"
