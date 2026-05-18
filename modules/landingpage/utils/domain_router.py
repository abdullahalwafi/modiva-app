from typing import Any


DOMAINS = {"edu_anemia_ttd", "program_policy", "hb_records", "fallback_none"}


def route_domain(intent_result: dict[str, Any]) -> dict[str, Any]:
    intent = str(intent_result.get("intent") or "").strip()
    recommended = str(intent_result.get("recommended_domain") or "").strip()
    reason = str(intent_result.get("reason") or "")

    if intent in {"smalltalk", "identity", "unclear_gibberish", "out_of_scope"}:
        return {
            "domain": "fallback_none",
            "retrieval_allowed": False,
            "retrieval_strategy": "none",
            "reason": f"Intent {intent} tidak membutuhkan retrieval.",
        }

    if intent == "symptom_or_diagnostic":
        return {
            "domain": "fallback_none",
            "retrieval_allowed": False,
            "retrieval_strategy": "none",
            "reason": "Pertanyaan diagnosis personal dijawab dengan respons aman tanpa retrieval.",
        }

    if intent == "hb_record_query":
        return {
            "domain": "hb_records",
            "retrieval_allowed": True,
            "retrieval_strategy": "metadata_first",
            "reason": "Pertanyaan diarahkan ke data Hb siswa/siswi.",
        }

    if intent == "program_policy":
        return {
            "domain": "program_policy",
            "retrieval_allowed": True,
            "retrieval_strategy": "vector",
            "reason": "Pertanyaan diarahkan ke SOP, pedoman, jadwal, atau program TTD.",
        }

    if intent == "procedure_prevention":
        if recommended == "program_policy":
            return {
                "domain": "program_policy",
                "retrieval_allowed": True,
                "retrieval_strategy": "vector",
                "reason": "Pertanyaan prosedural lebih dekat ke domain program/pedoman.",
            }
        return {
            "domain": "edu_anemia_ttd",
            "retrieval_allowed": True,
            "retrieval_strategy": "vector",
            "reason": "Pertanyaan prosedur pencegahan diarahkan ke edukasi anemia/TTD.",
        }

    if intent in {"definition", "education_faq"}:
        return {
            "domain": "edu_anemia_ttd",
            "retrieval_allowed": True,
            "retrieval_strategy": "vector",
            "reason": "Pertanyaan edukatif diarahkan ke domain edukasi anemia/TTD.",
        }

    if recommended in DOMAINS - {"fallback_none"}:
        return {
            "domain": recommended,
            "retrieval_allowed": True,
            "retrieval_strategy": "metadata_first" if recommended == "hb_records" else "vector",
            "reason": reason or "Domain mengikuti rekomendasi intent router.",
        }

    return {
        "domain": "fallback_none",
        "retrieval_allowed": False,
        "retrieval_strategy": "none",
        "reason": "Domain tidak cocok dengan cakupan RAG MODIVA.",
    }
