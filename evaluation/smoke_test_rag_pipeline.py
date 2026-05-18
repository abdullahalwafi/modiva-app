from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from modules.landingpage.utils.context_builder import build_context_for_query
from modules.landingpage.utils.domain_router import route_domain
from modules.landingpage.utils.grounding_judge import judge_grounding
from modules.landingpage.utils.intent_router import route_intent
from modules.landingpage.utils.response_generator import generate_response


QUESTIONS = [
    "Halo",
    "Apa itu anemia?",
    "Gejala anemia apa saja?",
    "TTD diminum berapa kali?",
    "Saya pusing, apakah saya anemia?",
    "asdsadasfa",
    "Hb siswi Ani tahun 2024 berapa?",
    "Siapa presiden Amerika?",
]


def run_pipeline(question: str) -> dict[str, Any]:
    intent_result = route_intent(question)
    domain_result = route_domain(intent_result)
    if domain_result.get("retrieval_allowed"):
        context_result = build_context_for_query(
            question=question,
            domain=str(domain_result.get("domain") or "fallback_none"),
            intent=str(intent_result.get("intent") or ""),
            mode="chatbot_public",
            top_k=5,
        )
    else:
        context_result = {
            "chunks": [],
            "domain": domain_result.get("domain", "fallback_none"),
            "retrieval_confidence": 0.0,
            "retrieval_summary": "Retrieval skipped by domain router.",
            "error": None,
        }
    grounding_result = judge_grounding(
        question=question,
        intent=str(intent_result.get("intent") or ""),
        domain=str(domain_result.get("domain") or "fallback_none"),
        context_result=context_result,
        mode="chatbot_public",
    )
    generated = generate_response(
        question=question,
        intent_result=intent_result,
        domain_result=domain_result,
        context_result=context_result,
        grounding_result=grounding_result,
        mode="chatbot_public",
    )
    return {
        "question": question,
        "intent": intent_result.get("intent"),
        "domain": domain_result.get("domain"),
        "retrieval_allowed": domain_result.get("retrieval_allowed"),
        "retrieval_confidence": context_result.get("retrieval_confidence"),
        "answerable": grounding_result.get("is_answerable"),
        "abstention_type": grounding_result.get("abstention_type"),
        "answer": generated.get("answer"),
        "context_error": context_result.get("error"),
    }


def check_result(result: dict[str, Any]) -> tuple[bool, str]:
    question = result["question"]
    intent = result["intent"]
    domain = result["domain"]
    answer = str(result.get("answer") or "").lower()

    if question == "Halo":
        return intent == "smalltalk" and not result["retrieval_allowed"], "smalltalk tanpa retrieval"
    if question == "Apa itu anemia?":
        return intent == "definition" and domain == "edu_anemia_ttd", "definisi ke edu_anemia_ttd"
    if question == "Gejala anemia apa saja?":
        return intent == "education_faq" and domain == "edu_anemia_ttd", "FAQ edukasi ke edu_anemia_ttd"
    if question == "TTD diminum berapa kali?":
        return intent in {"program_policy", "procedure_prevention"} and domain in {"program_policy", "edu_anemia_ttd"}, "TTD ke program/prosedur"
    if question == "Saya pusing, apakah saya anemia?":
        ok = intent == "symptom_or_diagnostic" and result["abstention_type"] == "needs_medical_confirmation" and "hb" in answer
        return ok, "diagnosis personal aman dan menyebut pemeriksaan Hb"
    if question == "asdsadasfa":
        return intent == "unclear_gibberish" and not result["retrieval_allowed"], "input ngawur tanpa retrieval"
    if question == "Hb siswi Ani tahun 2024 berapa?":
        return intent == "hb_record_query" and domain == "hb_records", "query Hb ke hb_records"
    if question == "Siapa presiden Amerika?":
        return intent == "out_of_scope" and not result["retrieval_allowed"], "out_of_scope tanpa retrieval"
    return True, "no check"


def main() -> None:
    failures = 0
    for question in QUESTIONS:
        result = run_pipeline(question)
        ok, note = check_result(result)
        if not ok:
            failures += 1
        print(json.dumps({"ok": ok, "note": note, **result}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
