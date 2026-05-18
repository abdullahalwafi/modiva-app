import re
from typing import Any


def _low(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _low(text))


def _contains_any(text: str, terms: list[str]) -> bool:
    low = _low(text)
    return any(term in low for term in terms)


def _query_keywords(question: str) -> set[str]:
    stopwords = {
        "apa",
        "itu",
        "yang",
        "dengan",
        "untuk",
        "dan",
        "atau",
        "di",
        "ke",
        "dari",
        "berapa",
        "bagaimana",
        "gimana",
        "saja",
        "adalah",
        "apakah",
        "saya",
        "aku",
        "the",
        "a",
        "an",
    }
    return {token for token in _tokenize(question) if len(token) >= 3 and token not in stopwords}


def _extract_hb_constraints(question: str) -> tuple[set[str], set[str]]:
    q = _low(question)
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", q))
    ignored = {
        "hb",
        "hemoglobin",
        "siswi",
        "siswa",
        "tahun",
        "sekolah",
        "data",
        "hasil",
        "pemeriksaan",
        "berapa",
        "kadar",
        "status",
        "nilai",
        "rekam",
        "nama",
        "nis",
    }
    names = {
        token
        for token in _tokenize(q)
        if len(token) >= 3 and token not in ignored and not re.fullmatch(r"\d+", token)
    }
    return names, years


def _chunk_domain_matches(chunk: dict[str, Any], domain: str) -> bool:
    if domain == "fallback_none":
        return True
    chunk_domain = str(chunk.get("domain") or chunk.get("metadata", {}).get("domain") or "")
    return chunk_domain == domain


def _has_definition_evidence(question: str, chunk_text: str) -> bool:
    q_terms = _query_keywords(question)
    text = _low(chunk_text)
    has_subject = any(term in text for term in q_terms) if q_terms else True
    definition_markers = [
        " adalah ",
        " merupakan ",
        " didefinisikan ",
        " pengertian ",
        " kondisi ",
        " keadaan ",
        " kurang darah ",
        " kadar hemoglobin ",
    ]
    return has_subject and any(marker in f" {text} " for marker in definition_markers)


def _has_education_evidence(question: str, chunk_text: str) -> bool:
    q_terms = _query_keywords(question)
    text = _low(chunk_text)
    overlap = sum(1 for term in q_terms if term in text)
    education_markers = [
        "anemia",
        "gejala",
        "penyebab",
        "pencegahan",
        "zat besi",
        "tablet tambah darah",
        "ttd",
        "hemoglobin",
        "remaja putri",
    ]
    return overlap >= 1 and _contains_any(text, education_markers)


def _has_procedure_evidence(question: str, chunk_text: str) -> bool:
    q_terms = _query_keywords(question)
    text = _low(chunk_text)
    overlap = sum(1 for term in q_terms if term in text)
    procedure_markers = [
        "diminum",
        "minum",
        "konsumsi",
        "seminggu",
        "minggu",
        "setiap",
        "jadwal",
        "aturan",
        "dosis",
        "distribusi",
        "monitoring",
        "program",
        "pedoman",
        "sop",
        "pencegahan",
        "makanan",
        "zat besi",
    ]
    return overlap >= 1 and _contains_any(text, procedure_markers)


def _has_hb_record_evidence(question: str, chunk_text: str) -> bool:
    text = _low(chunk_text)
    if not _contains_any(text, ["hb=", "hemoglobin", "kadar hb", "data: nama=", "status anemia"]):
        return False

    names, years = _extract_hb_constraints(question)
    if years and not all(year in text for year in years):
        return False
    if names and not any(name in text for name in names):
        return False
    return True


def judge_grounding(
    question: str,
    intent: str,
    domain: str,
    context_result: dict[str, Any],
    mode: str = "chatbot_public",
) -> dict[str, Any]:
    if intent == "smalltalk":
        return {
            "is_answerable": True,
            "confidence": 1.0,
            "abstention_type": None,
            "reason": "Smalltalk dijawab langsung tanpa retrieval.",
            "allowed_chunks": [],
        }

    if intent == "identity":
        return {
            "is_answerable": True,
            "confidence": 1.0,
            "abstention_type": None,
            "reason": "Identitas asisten dijawab langsung tanpa retrieval.",
            "allowed_chunks": [],
        }

    if intent == "unclear_gibberish":
        return {
            "is_answerable": False,
            "confidence": 0.0,
            "abstention_type": "unclear_question",
            "reason": "Pertanyaan tidak cukup jelas.",
            "allowed_chunks": [],
        }

    if intent == "symptom_or_diagnostic":
        return {
            "is_answerable": False,
            "confidence": 0.0,
            "abstention_type": "needs_medical_confirmation",
            "reason": "Diagnosis personal tidak boleh dijawab hanya dari gejala.",
            "allowed_chunks": [],
        }

    if intent == "out_of_scope":
        return {
            "is_answerable": False,
            "confidence": 0.0,
            "abstention_type": "out_of_scope",
            "reason": "Topik berada di luar cakupan MODIVA.",
            "allowed_chunks": [],
        }

    chunks = context_result.get("chunks") or []
    retrieval_confidence = float(context_result.get("retrieval_confidence") or 0.0)
    allowed_chunks = [chunk for chunk in chunks if _chunk_domain_matches(chunk, domain)]

    if not allowed_chunks:
        abstention = "no_matching_record" if intent == "hb_record_query" else "unknown_from_docs"
        return {
            "is_answerable": False,
            "confidence": retrieval_confidence,
            "abstention_type": abstention,
            "reason": "Tidak ada chunk domain yang cocok.",
            "allowed_chunks": [],
        }

    if retrieval_confidence < 0.22:
        abstention = "no_matching_record" if intent == "hb_record_query" else "unknown_from_docs"
        return {
            "is_answerable": False,
            "confidence": retrieval_confidence,
            "abstention_type": abstention,
            "reason": "Retrieval confidence terlalu rendah.",
            "allowed_chunks": [],
        }

    evidence_chunks: list[dict[str, Any]] = []
    for chunk in allowed_chunks:
        text = str(chunk.get("text") or "")
        if intent == "definition" and _has_definition_evidence(question, text):
            evidence_chunks.append(chunk)
        elif intent == "education_faq" and _has_education_evidence(question, text):
            evidence_chunks.append(chunk)
        elif intent in {"procedure_prevention", "program_policy"} and _has_procedure_evidence(question, text):
            evidence_chunks.append(chunk)
        elif intent == "hb_record_query" and _has_hb_record_evidence(question, text):
            evidence_chunks.append(chunk)

    if not evidence_chunks:
        abstention = "no_matching_record" if intent == "hb_record_query" else "unknown_from_docs"
        return {
            "is_answerable": False,
            "confidence": retrieval_confidence,
            "abstention_type": abstention,
            "reason": "Chunk teratas belum mengandung bukti yang cukup untuk intent.",
            "allowed_chunks": [],
        }

    confidence = min(1.0, max(retrieval_confidence, float(evidence_chunks[0].get("score") or 0.0)))
    return {
        "is_answerable": True,
        "confidence": confidence,
        "abstention_type": None,
        "reason": "Ada chunk domain yang relevan dan cukup menjawab intent.",
        "allowed_chunks": evidence_chunks,
    }
