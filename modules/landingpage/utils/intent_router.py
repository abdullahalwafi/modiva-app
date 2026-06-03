import re
from typing import Any


INTENTS = {
    "smalltalk",
    "identity",
    "unclear_gibberish",
    "definition",
    "education_faq",
    "procedure_prevention",
    "program_policy",
    "hb_record_query",
    "mapping_navigation",
    "symptom_or_diagnostic",
    "out_of_scope",
}


def _normalize(text: str) -> str:
    text = str(text or "").strip().lower()
    text = re.sub(r"[^a-z0-9%/.,\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _is_unclear_gibberish(text: str) -> bool:
    normalized = _normalize(text)
    if not normalized:
        return True

    meaningful_short = {
        "hb",
        "ttd",
        "anemia",
        "halo",
        "hai",
        "hi",
        "pagi",
        "siang",
        "sore",
        "malam",
    }
    if normalized in meaningful_short:
        return False

    tokens = normalized.split()
    if len(normalized) <= 2:
        return True

    if len(tokens) == 1:
        token = tokens[0]
        if len(token) >= 7 and not re.search(r"[aiueo]", token):
            return True
        if len(token) >= 8 and token.isalpha():
            distinct_ratio = len(set(token)) / max(len(token), 1)
            vowel_ratio = sum(1 for ch in token if ch in "aiueo") / len(token)
            if distinct_ratio < 0.45 or vowel_ratio < 0.2:
                return True

    letters = re.sub(r"[^a-z]", "", normalized)
    if len(letters) >= 8:
        vowel_ratio = sum(1 for ch in letters if ch in "aiueo") / len(letters)
        if vowel_ratio < 0.15:
            return True

    return False


def route_intent(question: str) -> dict[str, Any]:
    """
    Rule-based router for MODIVA RAG.

    Diagnosis-like personal questions are checked before generic anemia rules so
    the system never treats a personal symptom report as a normal FAQ.
    """
    q = _normalize(question)

    if _is_unclear_gibberish(q):
        return {
            "intent": "unclear_gibberish",
            "confidence": 0.92,
            "recommended_domain": "fallback_none",
            "response_mode": "clarify",
            "reason": "Input kosong, terlalu pendek, atau tidak terbaca sebagai pertanyaan bermakna.",
        }

    smalltalk_inputs = {
        "halo",
        "hallo",
        "hai",
        "hi",
        "hello",
        "assalamualaikum",
        "selamat pagi",
        "selamat siang",
        "selamat sore",
        "selamat malam",
        "pagi",
        "siang",
        "sore",
        "malam",
        "terima kasih",
        "makasih",
        "thanks",
    }
    if q in smalltalk_inputs:
        return {
            "intent": "smalltalk",
            "confidence": 0.98,
            "recommended_domain": "fallback_none",
            "response_mode": "direct",
            "reason": "Input adalah salam atau pembuka percakapan.",
        }

    identity_patterns = [
        r"\bsiapa kamu\b",
        r"\bsiapa anda\b",
        r"\bkamu siapa\b",
        r"\banda siapa\b",
        r"\bini chatbot apa\b",
        r"\bchatbot apa\b",
        r"\bkamu apa\b",
        r"\basisten apa\b",
        r"\bmodiva itu apa\b",
    ]
    if _matches_any(q, identity_patterns):
        return {
            "intent": "identity",
            "confidence": 0.96,
            "recommended_domain": "fallback_none",
            "response_mode": "direct",
            "reason": "Pertanyaan menanyakan identitas atau fungsi asisten.",
        }

    personal_symptom_patterns = [
        r"\b(saya|aku|diriku|anak saya|teman saya)\b.*\b(pusing|lemas|capek|lelah|lesu|pucat|berkunang|sesak|berdebar|kunang)\b",
        r"\b(apakah|apa)\s+(saya|aku|anak saya)\s+(terkena|kena|mengalami|menderita)?\s*anemia\b",
        r"\b(saya|aku|anak saya)\b.*\b(anemia|kurang darah)\b",
        r"\bsering\b.*\b(pusing|lemas|capek|lelah|lesu|pucat)\b",
    ]
    if _matches_any(q, personal_symptom_patterns):
        return {
            "intent": "symptom_or_diagnostic",
            "confidence": 0.94,
            "recommended_domain": "fallback_none",
            "response_mode": "safe_medical",
            "reason": "Pertanyaan berisi gejala personal atau permintaan diagnosis.",
        }

    mapping_terms = [
        "peta",
        "pemetaan",
        "map",
        "maps",
        "lokasi",
        "persebaran",
        "sebaran",
        "koordinat",
        "titik sekolah",
        "titik puskesmas",
        "wilayah",
    ]
    if _contains_any(q, mapping_terms) and _contains_any(
        q,
        ["peta", "pemetaan", "map", "maps", "lokasi", "sebaran", "persebaran", "koordinat"],
    ):
        return {
            "intent": "mapping_navigation",
            "confidence": 0.9,
            "recommended_domain": "fallback_none",
            "response_mode": "direct",
            "reason": "Pertanyaan mengarah ke fitur peta/pemetaan MODIVA, bukan dokumen RAG.",
        }

    hb_record_terms = [
        "data hb",
        "hasil hb",
        "hasil pemeriksaan",
        "rekam hb",
        "siswi",
        "siswa",
        "nis",
        "sekolah",
        "tahun",
        "berapa hb",
        "kadar hb",
        "status hb",
        "status anemia",
    ]
    has_hb_word = bool(re.search(r"\b(hb|hemoglobin)\b", q))
    is_hb_definition = has_hb_word and _matches_any(
        q,
        [
            r"\bapa itu\s+(hb|hemoglobin)\b",
            r"\bdefinisi\s+(hb|hemoglobin)\b",
            r"\bpengertian\s+(hb|hemoglobin)\b",
        ],
    )
    if has_hb_word and not is_hb_definition and _contains_any(q, hb_record_terms):
        return {
            "intent": "hb_record_query",
            "confidence": 0.9,
            "recommended_domain": "hb_records",
            "response_mode": "data",
            "reason": "Pertanyaan meminta data atau hasil pemeriksaan Hb.",
        }

    definition_patterns = [
        r"\bapa itu\b",
        r"\bapa yang dimaksud\b",
        r"\bpengertian\b",
        r"\bdefinisi\b",
        r"\barti\b",
        r"\bdidefinisikan\b",
    ]
    if _matches_any(q, definition_patterns) and _contains_any(
        q,
        ["anemia", "ttd", "tablet tambah darah", "hb", "hemoglobin", "kurang darah"],
    ):
        return {
            "intent": "definition",
            "confidence": 0.9,
            "recommended_domain": "edu_anemia_ttd",
            "response_mode": "grounded",
            "reason": "Pertanyaan meminta definisi istilah anemia/TTD/Hb.",
        }

    program_terms = [
        "program",
        "pedoman",
        "sop",
        "kebijakan",
        "distribusi",
        "monitoring",
        "jadwal",
        "berapa kali",
        "seminggu",
        "mingguan",
        "aturan konsumsi",
        "aturan minum",
        "diminum berapa",
        "tablet tambah darah",
        "ttd",
        "sekolah",
        "puskesmas",
    ]
    if _contains_any(q, program_terms) and _contains_any(
        q,
        ["ttd", "tablet tambah darah", "program", "pedoman", "sop", "distribusi", "monitoring"],
    ):
        return {
            "intent": "program_policy",
            "confidence": 0.86,
            "recommended_domain": "program_policy",
            "response_mode": "grounded",
            "reason": "Pertanyaan mengarah ke aturan, jadwal, atau program TTD.",
        }

    prevention_terms = [
        "pencegahan",
        "mencegah",
        "cara cegah",
        "cara mencegah",
        "cara minum",
        "konsumsi",
        "diminum",
        "minum ttd",
        "makanan",
        "zat besi",
        "gizi",
        "vitamin",
        "tablet tambah darah",
        "ttd",
    ]
    if _contains_any(q, prevention_terms):
        return {
            "intent": "procedure_prevention",
            "confidence": 0.84,
            "recommended_domain": "edu_anemia_ttd",
            "response_mode": "grounded",
            "reason": "Pertanyaan meminta cara pencegahan, konsumsi, atau tindakan edukatif.",
        }

    education_terms = [
        "gejala",
        "ciri",
        "penyebab",
        "dampak",
        "risiko",
        "resiko",
        "faktor",
        "tanda",
        "anemia",
        "kurang darah",
        "zat besi",
        "remaja putri",
        "mengapa",
        "kenapa",
    ]
    if _contains_any(q, education_terms):
        return {
            "intent": "education_faq",
            "confidence": 0.82,
            "recommended_domain": "edu_anemia_ttd",
            "response_mode": "grounded",
            "reason": "Pertanyaan termasuk FAQ edukasi anemia/TTD.",
        }

    if has_hb_word:
        return {
            "intent": "hb_record_query",
            "confidence": 0.72,
            "recommended_domain": "hb_records",
            "response_mode": "data",
            "reason": "Pertanyaan menyebut Hb dan berpotensi meminta data pemeriksaan.",
        }

    return {
        "intent": "out_of_scope",
        "confidence": 0.78,
        "recommended_domain": "fallback_none",
        "response_mode": "abstain",
        "reason": "Topik tidak terdeteksi sebagai anemia, TTD, Hb, atau MODIVA.",
    }
