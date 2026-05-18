import re
from typing import Any


SPECIAL_PUBLIC_RESPONSES = {
    "smalltalk": "Halo! Saya asisten MODIVA. Saya bisa membantu menjawab pertanyaan seputar anemia, Tablet Tambah Darah (TTD), dan informasi Hb yang tersedia.",
    "identity": "Saya asisten MODIVA yang membantu memberikan informasi seputar anemia, Tablet Tambah Darah (TTD), dan data Hb yang tersedia di sistem.",
    "unclear_question": "Maaf, saya belum memahami pertanyaannya. Bisa tuliskan ulang dengan lebih jelas?",
    "needs_medical_confirmation": "Saya belum bisa memastikan apakah Anda anemia hanya dari gejala. Anemia biasanya perlu dipastikan melalui pemeriksaan kadar Hb. Jika keluhan seperti pusing, lemas, atau mudah lelah sering terjadi, sebaiknya periksa Hb atau konsultasikan ke tenaga kesehatan.",
    "out_of_scope": "Maaf, saya hanya bisa membantu pertanyaan seputar anemia, Tablet Tambah Darah (TTD), dan data Hb yang tersedia di MODIVA.",
    "unknown_from_docs": "Saya belum menemukan informasi yang cukup dari dokumen MODIVA untuk menjawab pertanyaan itu dengan pasti.",
    "no_matching_record": "Saya belum menemukan data Hb yang cocok dengan pertanyaan tersebut. Coba sertakan nama, tahun, sekolah, atau informasi pemeriksaan yang lebih spesifik.",
}


def _clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -•\t\r\n")


def _split_sentences(text: str) -> list[str]:
    clean = _clean_text(text)
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return [part.strip() for part in parts if part.strip()]


def _keywords(question: str) -> set[str]:
    stop = {
        "apa",
        "itu",
        "yang",
        "dengan",
        "untuk",
        "dan",
        "atau",
        "berapa",
        "bagaimana",
        "apakah",
        "saja",
        "saya",
        "aku",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(question or "").lower())
        if len(token) >= 3 and token not in stop
    }


def _best_sentences(question: str, chunks: list[dict[str, Any]], limit: int = 2) -> list[str]:
    q_terms = _keywords(question)
    ranked: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    index = 0
    for chunk in chunks:
        for sentence in _split_sentences(str(chunk.get("text") or "")):
            key = sentence.lower()
            if key in seen:
                continue
            seen.add(key)
            low = key
            score = sum(2 for term in q_terms if term in low)
            if " adalah " in f" {low} " or " merupakan " in f" {low} ":
                score += 2
            if any(marker in low for marker in ["data: nama=", "hb=", "hemoglobin"]):
                score += 2
            if any(marker in low for marker in ["diminum", "konsumsi", "seminggu", "jadwal"]):
                score += 2
            ranked.append((-score, index, sentence))
            index += 1

    ranked.sort()
    selected = [sentence for _, _, sentence in ranked[:limit] if sentence]
    if selected:
        return selected
    fallback = [_clean_text(str(chunk.get("text") or "")) for chunk in chunks if _clean_text(str(chunk.get("text") or ""))]
    return fallback[:limit]


def _definition_sentence(question: str, chunks: list[dict[str, Any]]) -> str:
    q_terms = _keywords(question)
    definition_verbs = r"(?:adalah|merupakan|didefinisikan sebagai)"
    for chunk in chunks:
        text = _clean_text(str(chunk.get("text") or ""))
        for term in q_terms:
            match = re.search(
                rf"\b({re.escape(term)}\s+{definition_verbs}[^.?!]*[.?!]?)",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                snippet = match.group(1).strip()
                return snippet[:1].upper() + snippet[1:]
    return ""


def _source_label(chunk: dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return str(
        chunk.get("source")
        or meta.get("source_doc")
        or meta.get("title")
        or meta.get("doc_id")
        or meta.get("source")
        or ""
    ).strip()


def _collect_sources(chunks: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        source = _source_label(chunk)
        if source and source not in seen:
            seen.add(source)
            sources.append(source)
    return sources


def _parse_hb_record(text: str) -> dict[str, str]:
    data_match = re.search(r"data:\s*(.+)$", text, flags=re.IGNORECASE | re.DOTALL)
    raw = data_match.group(1) if data_match else text
    record: dict[str, str] = {}
    for key in ["nama", "nis", "sekolah", "tahun", "hb", "keterangan", "status"]:
        match = re.search(rf"{key}\s*=\s*([^,\n.]+)", raw, flags=re.IGNORECASE)
        if match:
            record[key] = match.group(1).strip()
    if "status" not in record and "keterangan" in record:
        record["status"] = record["keterangan"]
    return record


def _format_hb_records(chunks: list[dict[str, Any]], mode: str) -> str:
    records = []
    for chunk in chunks:
        record = _parse_hb_record(str(chunk.get("text") or ""))
        meta = chunk.get("metadata") or {}
        if not record:
            record = {
                "nama": str(meta.get("nama") or ""),
                "nis": str(meta.get("nis") or ""),
                "sekolah": str(meta.get("sekolah") or ""),
                "tahun": str(meta.get("tahun") or ""),
                "hb": str(meta.get("hb") or ""),
                "status": str(meta.get("status") or meta.get("keterangan") or ""),
            }
        if any(record.values()):
            records.append(record)

    if not records:
        return " ".join(_best_sentences("", chunks, limit=2)).strip()

    lines = []
    for record in records[:5]:
        parts = []
        if record.get("nama"):
            parts.append(f"Nama: {record['nama']}")
        if record.get("nis"):
            parts.append(f"NIS: {record['nis']}")
        if record.get("sekolah"):
            parts.append(f"Sekolah: {record['sekolah']}")
        if record.get("tahun"):
            parts.append(f"Tahun: {record['tahun']}")
        if record.get("hb"):
            parts.append(f"Hb: {record['hb']}")
        if record.get("status"):
            parts.append(f"Status: {record['status']}")
        lines.append("; ".join(parts))

    if mode == "evaluation_strict":
        return " | ".join(lines)
    return "\n".join(f"- {line}" for line in lines)


def _abstention_answer(intent: str, abstention_type: str | None, mode: str) -> str:
    if mode == "evaluation_strict":
        return "UNKNOWN"
    if intent in {"smalltalk", "identity"}:
        return SPECIAL_PUBLIC_RESPONSES[intent]
    return SPECIAL_PUBLIC_RESPONSES.get(
        abstention_type or "",
        SPECIAL_PUBLIC_RESPONSES["unknown_from_docs"],
    )


def generate_response(
    question: str,
    intent_result: dict[str, Any],
    domain_result: dict[str, Any],
    context_result: dict[str, Any],
    grounding_result: dict[str, Any],
    mode: str = "chatbot_public",
) -> dict[str, Any]:
    mode = mode if mode in {"chatbot_public", "evaluation_strict", "internal_data"} else "chatbot_public"
    intent = str(intent_result.get("intent") or "")
    domain = str(domain_result.get("domain") or "")
    answerable = bool(grounding_result.get("is_answerable"))
    abstention_type = grounding_result.get("abstention_type")
    allowed_chunks = grounding_result.get("allowed_chunks") or []
    sources = _collect_sources(allowed_chunks)

    if not answerable:
        answer = _abstention_answer(intent, abstention_type, mode)
    elif intent in {"smalltalk", "identity"}:
        answer = SPECIAL_PUBLIC_RESPONSES[intent]
        if mode == "evaluation_strict":
            answer = answer.replace("Halo! ", "").strip()
    elif domain == "hb_records" or mode == "internal_data":
        answer = _format_hb_records(allowed_chunks, mode)
        if mode == "chatbot_public" and answer:
            answer = f"Data Hb yang cocok:\n{answer}"
    else:
        sentence_limit = 1 if mode == "evaluation_strict" else 2
        if intent == "definition":
            definition = _definition_sentence(question, allowed_chunks)
            sentences = [definition] if definition else _best_sentences(question, allowed_chunks, limit=sentence_limit)
        else:
            sentences = _best_sentences(question, allowed_chunks, limit=sentence_limit)
        answer = " ".join(sentences).strip()
        if not answer:
            answer = "UNKNOWN" if mode == "evaluation_strict" else SPECIAL_PUBLIC_RESPONSES["unknown_from_docs"]

    if mode == "chatbot_public" and len(answer.split()) > 120:
        words = answer.split()
        answer = " ".join(words[:120]).rstrip(" ,;") + "..."

    return {
        "answer": answer,
        "mode": mode,
        "intent": intent,
        "domain": domain,
        "answerable": answerable,
        "abstention_type": abstention_type,
        "sources": sources,
        "debug": {
            "intent": intent_result,
            "domain": domain_result,
            "grounding": {
                "confidence": grounding_result.get("confidence"),
                "reason": grounding_result.get("reason"),
            },
            "retrieval": {
                "confidence": context_result.get("retrieval_confidence"),
                "summary": context_result.get("retrieval_summary"),
                "error": context_result.get("error"),
            },
        },
    }
