import io
import re
from collections import Counter

import pandas as pd
from docx import Document as DocxDocument
from pypdf import PdfReader


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", str(line)).strip()


def _is_page_noise(line: str) -> bool:
    text = _normalize_line(line)
    if not text:
        return True

    words = text.split()
    alpha_chars = [ch for ch in text if ch.isalpha()]
    upper_ratio = (
        sum(1 for ch in alpha_chars if ch.isupper()) / len(alpha_chars)
        if alpha_chars else 0.0
    )

    if re.fullmatch(r"[\divxlcdmIVXLCDM.\-–\s]+", text):
        return True
    if len(words) <= 2 and any(ch.isdigit() for ch in text):
        return True
    if upper_ratio > 0.75 and len(words) <= 14 and not re.search(r"[.?!:]$", text):
        return True
    if text.count("|") >= 1 and len(words) <= 20:
        return True
    return False


def _merge_broken_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    buffer = ""

    for raw_line in lines:
        line = _normalize_line(raw_line)
        if not line:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            continue

        if not buffer:
            buffer = line
            continue

        if re.search(r"[.?!:]$", buffer):
            merged.append(buffer.strip())
            buffer = line
        else:
            buffer = f"{buffer} {line}"

    if buffer:
        merged.append(buffer.strip())

    return merged


def _chunk_text_blocks(blocks: list[str], max_chars: int = 900) -> list[str]:
    chunks: list[str] = []
    current = ""

    for block in blocks:
        block = _normalize_line(block)
        if not block:
            continue

        if len(block) > max_chars:
            sentences = [
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+", block)
                if s.strip()
            ]
            for sentence in sentences:
                if not current:
                    current = sentence
                elif len(current) + 1 + len(sentence) <= max_chars:
                    current = f"{current} {sentence}"
                else:
                    chunks.append(current.strip())
                    current = sentence
            continue

        if not current:
            current = block
        elif len(current) + 2 + len(block) <= max_chars:
            current = f"{current}\n\n{block}"
        else:
            chunks.append(current.strip())
            current = block

    if current:
        chunks.append(current.strip())

    return chunks


def _extract_pdf_rows(uploaded_file) -> list[str]:
    uploaded_file.seek(0)
    reader = PdfReader(io.BytesIO(uploaded_file.read()))

    pages_lines: list[list[str]] = []
    freq_counter: Counter[str] = Counter()

    for page in reader.pages:
        text = page.extract_text() or ""
        raw_lines = [line for line in text.splitlines()]
        lines = [_normalize_line(line) for line in raw_lines if _normalize_line(line)]
        pages_lines.append(lines)
        for line in lines:
            freq_counter[line] += 1

    extracted_rows: list[str] = []
    for lines in pages_lines:
        filtered = []
        for line in lines:
            if _is_page_noise(line):
                continue
            if freq_counter[line] >= 2 and len(line.split()) <= 18:
                continue
            filtered.append(line)

        merged_blocks = _merge_broken_lines(filtered)
        extracted_rows.extend(_chunk_text_blocks(merged_blocks))

    return extracted_rows


def _extract_docx_rows(uploaded_file) -> list[str]:
    uploaded_file.seek(0)
    file_stream = io.BytesIO(uploaded_file.read())
    doc = DocxDocument(file_stream)
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return _chunk_text_blocks(paragraphs, max_chars=900)


def _extract_excel_rows(uploaded_file) -> list[str]:
    uploaded_file.seek(0)
    try:
        xls = pd.read_excel(
            uploaded_file,
            sheet_name=None,
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
        )
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_excel(
            uploaded_file,
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
        )
        xls = {"Sheet1": df}

    extracted_rows: list[str] = []
    for _, df in xls.items():
        df = df.fillna("")
        headers = [str(c).strip() for c in df.columns]
        for _, row in df.iterrows():
            pairs = []
            for h, v in zip(headers, row):
                if str(v).strip():
                    pairs.append(f"{h}: {v}")
            if pairs:
                extracted_rows.append(", ".join(pairs))
    return extracted_rows


def extract_text_from_file(uploaded_file):
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return _extract_pdf_rows(uploaded_file)

    if filename.endswith(".docx"):
        return _extract_docx_rows(uploaded_file)

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return _extract_excel_rows(uploaded_file)

    raise ValueError("Format file tidak didukung.")
