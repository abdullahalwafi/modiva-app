# modules/landingpage/views.py
import json
import os
import re

import numpy as np
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from modules.landingpage.models import ContactMessage
from .forms import ContactMessageForm
from modules.vitamin.models import Puskesmas, Sekolah

from .utils.chroma import get_collection
from .utils.context_builder import build_context_for_query, build_context_fullscan
from .utils.domain_router import route_domain
from .utils.keywords import extract_keywords
from .utils.intent_router import route_intent
from .utils.grounding_judge import judge_grounding
from .utils.response_generator import generate_response
from modules.vector.utils.chroma import get_docs_collection
from modules.vector.utils.embedding import get_model
from .utils.gemini import ask_gemini


UNKNOWN_REPLY = "Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen."
CHATBOT_NAME = "DIVA"


def _extract_gemini_text(payload: dict) -> str:
    try:
        candidates = payload.get("candidates", []) or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts", []) or []
            chunks = []
            for part in parts:
                text = part.get("text")
                if text:
                    chunks.append(str(text))
            if chunks:
                return "\n".join(chunks).strip()
    except Exception:
        return ""
    return ""


def _split_text_units(text: str) -> list[str]:
    normalized = re.sub(r"(?<![.!?])\s*\n\s*", " ", str(text))
    units: list[str] = []
    for block in re.split(r"[\n\r]+", normalized):
        block = block.strip()
        if not block:
            continue
        parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", block) if s.strip()]
        units.extend(parts or [block])
    return units


def _clean_answer_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text)).strip(" -•\t\r\n")
    cleaned = re.sub(r"\b\d+\s+BUKU SAKU\b", "BUKU SAKU", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _extract_definition_subject(question: str) -> str:
    q = _clean_answer_text(question).rstrip("?.! ").strip()
    q = re.sub(r"(?i)\b(si|sih)\b", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    patterns = [
        r"(?i)^apa itu\s+(.+)$",
        r"(?i)^apa yang dimaksud dengan\s+(.+)$",
        r"(?i)^apa yang dimaksud\s+dengan\s+(.+)$",
        r"(?i)^yang dimaksud dengan\s+(.+?)\s+apa$",
        r"(?i)^sebenarnya\s+(.+?)\s+itu\s+apa$",
        r"(?i)^sebenernya\s+(.+?)\s+itu\s+apa$",
        r"(?i)^(.+?)\s+itu\s+apa$",
        r"(?i)^yang dimaksud\s+(.+?)\s+apa$",
        r"(?i)^yang dimaksud dengan\s+(.+)$",
        r"(?i)^definisi\s+(.+)$",
        r"(?i)^arti\s+(.+)$",
    ]
    subject = ""
    for pattern in patterns:
        match = re.match(pattern, q)
        if match:
            subject = match.group(1).strip()
            break
    if not subject:
        return ""
    subject = re.sub(r"\s+", " ", subject)
    return subject


def _extract_topic_subject(question: str) -> str:
    q = _clean_answer_text(question).rstrip("?.! ").strip()
    q = re.sub(r"(?i)\b(si|sih)\b", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    patterns = [
        r"(?i)^tentang\s+(.+)$",
        r"(?i)^mengenai\s+(.+)$",
        r"(?i)^saya ingin tahu tentang\s+(.+)$",
        r"(?i)^saya ingiin tau tentang\s+(.+)$",
        r"(?i)^saya ingin tau tentang\s+(.+)$",
        r"(?i)^saya mau tahu tentang\s+(.+)$",
        r"(?i)^aku ingin tahu tentang\s+(.+)$",
        r"(?i)^aku mau tahu tentang\s+(.+)$",
        r"(?i)^ingin tahu tentang\s+(.+)$",
        r"(?i)^ingin tau tentang\s+(.+)$",
        r"(?i)^mau tahu tentang\s+(.+)$",
        r"(?i)^mau tau tentang\s+(.+)$",
        r"(?i)^jelaskan\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, q)
        if match:
            return re.sub(r"\s+", " ", match.group(1).strip())
    return ""


def _canonicalize_question(question: str) -> str:
    subject = _extract_definition_subject(question)
    if subject:
        return f"apa itu {subject}?"
    topic_subject = _extract_topic_subject(question)
    if topic_subject:
        return f"apa itu {topic_subject}?"
    return question.strip()


def _normalize_simple_text(text: str) -> str:
    cleaned = _clean_answer_text(text).lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _handle_smalltalk(question: str) -> str:
    normalized = _normalize_simple_text(question)
    if not normalized:
        return ""

    greeting_inputs = {
        "halo", "hallo", "hai", "hi", "hei", "hello", "pagi", "siang", "sore", "malam"
    }
    if normalized in greeting_inputs:
        return f"Halo, saya {CHATBOT_NAME}. Saya bisa bantu jelaskan informasi seputar anemia dan kesehatan dari dokumen yang tersedia."

    identity_patterns = [
        r"^dengan siapa ini$",
        r"^ini siapa$",
        r"^siapa ini$",
        r"^kamu siapa$",
        r"^anda siapa$",
        r"^siapa namamu$",
        r"^nama kamu siapa$",
    ]
    if any(re.match(pattern, normalized) for pattern in identity_patterns):
        return f"Saya {CHATBOT_NAME}, asisten yang bisa membantu menjelaskan informasi kesehatan dari dokumen yang tersedia."

    thanks_inputs = {"terima kasih", "makasih", "thanks", "thank you"}
    if normalized in thanks_inputs:
        return "Sama-sama. Kalau mau, saya bisa bantu jelaskan anemia, gejalanya, penyebabnya, atau cara pencegahannya."

    return ""


def _is_gibberish_text(question: str) -> bool:
    normalized = _normalize_simple_text(question)
    if not normalized:
        return True

    tokens = normalized.split()
    if len(tokens) == 1:
        token = tokens[0]
        if len(token) >= 7 and not re.search(r"[aiueo]", token):
            return True
        if len(token) >= 8:
            distinct_ratio = len(set(token)) / max(len(token), 1)
            if distinct_ratio < 0.6:
                return True
        if len(token) >= 8 and token.isalpha():
            vowel_ratio = sum(1 for ch in token if ch in "aiueo") / len(token)
            if vowel_ratio < 0.2:
                return True

    letters = re.sub(r"[^a-z]", "", normalized)
    if letters and len(letters) >= 8:
        vowel_ratio = sum(1 for ch in letters if ch in "aiueo") / len(letters)
        if vowel_ratio < 0.15:
            return True

    return False


def _handle_unclear_input(question: str) -> str:
    if _is_gibberish_text(question):
        return (
            "Maaf, saya belum paham pertanyaannya. "
            "Coba tulis ulang dengan kalimat yang lebih jelas, misalnya: apa itu anemia, apa gejala anemia, atau bagaimana cara mencegah anemia."
        )
    return ""


def _is_noisy_unit(text: str) -> bool:
    cleaned = _clean_answer_text(text)
    if not cleaned:
        return True

    low = cleaned.lower()
    words = cleaned.split()
    alpha_chars = [ch for ch in cleaned if ch.isalpha()]
    upper_ratio = (
        sum(1 for ch in alpha_chars if ch.isupper()) / len(alpha_chars)
        if alpha_chars else 0.0
    )

    generic_noise_markers = [
        "kata pengantar",
        "daftar isi",
        "lampiran",
        "gambar ",
        "tabel ",
        "bab ",
        "bagian ",
        "halaman ",
        "copyright",
    ]
    if any(marker in low for marker in generic_noise_markers):
        return True
    if re.fullmatch(r"[\divxlcdm.\-–\s]+", low):
        return True
    if len(words) <= 3 and any(ch.isdigit() for ch in cleaned):
        return True
    if upper_ratio > 0.72 and len(words) <= 16 and not re.search(r"[.?!]$", cleaned):
        return True
    if cleaned.count("|") >= 1 and len(words) <= 20:
        return True
    return False


def _rank_candidate_units(context_text: str, question: str, top_k: int = 5) -> list[str]:
    units = []
    seen = set()
    for unit in _split_text_units(context_text):
        cleaned = _clean_answer_text(unit)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        units.append(cleaned)

    if not units:
        return []

    keywords = [k.lower() for k in extract_keywords(question)]
    q_low = question.lower()

    lexical_scores = []
    filtered_units = []
    for unit in units:
        low = unit.lower()
        if _is_noisy_unit(unit):
            continue

        score = sum(2 for kw in keywords if kw and kw in low)
        score += sum(1 for token in re.findall(r"\w+", q_low) if len(token) >= 3 and token in low)
        if "%" in unit and any(token in q_low for token in ["berapa", "persentase", "presentase", "prevalensi", "%"]):
            score += 3
        if " adalah " in f" {low} " and any(token in q_low for token in ["apa itu", "apakah", "definisi", "arti"]):
            score += 2
        filtered_units.append(unit)
        lexical_scores.append(score)

    if not filtered_units:
        return []

    try:
        model = get_model()
        embeddings = np.array(model.encode(filtered_units), dtype=np.float32)
        q_emb = np.array(model.encode([question])[0], dtype=np.float32)
        norms = np.linalg.norm(embeddings, axis=1) + 1e-12
        q_norm = np.linalg.norm(q_emb) + 1e-12
        semantic_scores = (embeddings @ q_emb) / (norms * q_norm)
    except Exception:
        semantic_scores = np.zeros(len(filtered_units), dtype=np.float32)

    ranked = []
    for idx, unit in enumerate(filtered_units):
        final_score = (lexical_scores[idx] * 0.7) + (float(semantic_scores[idx]) * 10.0)
        ranked.append((final_score, idx, unit))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [unit for _, _, unit in ranked[:top_k]]


def _extract_best_snippet(text: str, question: str, max_sentences: int = 3) -> str:
    ranked = _rank_candidate_units(text, question, top_k=max_sentences)
    if ranked:
        return " ".join(ranked).strip()
    fallback_units = _split_text_units(text)
    return fallback_units[0].strip() if fallback_units else str(text).strip()


def _is_factoid_question(question: str) -> bool:
    q = question.lower()
    markers = [
        "berapa",
        "siapa",
        "apa itu",
        "apakah",
        "kapan",
        "dimana",
        "di mana",
        "prevalensi",
        "persentase",
        "presentase",
        "tujuan",
        "sumber",
        "risiko",
        "resiko",
    ]
    return any(marker in q for marker in markers)


def _extract_fact_answer(context_text: str, question: str) -> str:
    subject = _extract_definition_subject(question)
    if subject:
        units = _split_text_units(context_text)
        subject_pattern = re.escape(subject)
        for unit in units:
            cleaned = _clean_answer_text(unit)
            match = re.search(
                rf"((?:{subject_pattern}|[A-Z][a-z]+)\s+adalah[^.?!]*[.?!]?)",
                cleaned,
                flags=re.IGNORECASE,
            )
            if match and re.search(subject_pattern, match.group(1), flags=re.IGNORECASE):
                return _clean_answer_text(match.group(1))

    ranked = _rank_candidate_units(context_text, question, top_k=1)
    if ranked and _is_factoid_question(question):
        return ranked[0]
    return ""


# =========================
# PAGES
# =========================
def homepage(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("landingpage:pendaftaran_sukses")
    else:
        form = ContactMessageForm()
    return render(request, "index.html", {"form": form, "current_url": "home"})


def about_us(request):
    return render(request, "aboutUs.html", {"current_url": "about"})


def login(request):
    return render(request, "login.html")


def lupa_password(request):
    return render(request, "lupa_password.html")


def password_reset(request):
    return render(request, "password_reset.html")


def mitra(request):
    try:
        puskesmas2 = Puskesmas.objects.all().order_by("id")[:4]
        sekolah2 = Sekolah.objects.all().order_by("id")[:4]
    except Exception as e:
        puskesmas2 = None
        sekolah2 = None
        print(f"Error occurred: {e}")
    return render(request, "mitra.html", {"puskesmas2": puskesmas2, "sekolah2": sekolah2, "current_url": "mitra"})


def sk(request):
    return render(request, "sk.html", {"current_url": "sk"})


def privasi(request):
    return render(request, "privasi.html", {"current_url": "privasi"})


def puskesmas(request):
    try:
        puskesmas_list = Puskesmas.objects.all().order_by("id")
    except Exception as e:
        puskesmas_list = None
        print(f"Error occurred: {e}")
    return render(request, "puskesmas.html", {"puskesmas": puskesmas_list, "current_url": "puskesmas"})


def sekolah(request):
    try:
        sekolah_list = Sekolah.objects.all().order_by("id")
    except Exception as e:
        sekolah_list = None
        print(f"Error occurred: {e}")
    return render(request, "sekolah.html", {"sekolah": sekolah_list, "current_url": "sekolah"})


def profilpuskesmas(request, pk):
    puskesmas_obj = get_object_or_404(Puskesmas, id=pk)
    return render(request, "profil-puskesmas.html", {"puskesmas": puskesmas_obj, "current_url": "puskesmas"})


def profilsekolah(request, pk):
    sekolah_obj = get_object_or_404(Sekolah, id=pk)
    return render(request, "profil-sekolah.html", {"sekolah": sekolah_obj, "current_url": "sekolah"})


def coba(request):
    return render(request, "coba.html")


def daftar(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("landingpage:pendaftaran_sukses")
    else:
        form = ContactMessageForm()
    return render(request, "daftar.html", {"form": form, "current_url": "daftar"})


def pendaftaran_sukses(request):
    return render(request, "pendaftaran_sukses.html", {"current_url": "daftar"})


def mobile_app(request):
    return render(request, "mobile_app.html", {"current_url": "mobile_app"})


# =========================
# CHAT API (INTENT/DOMAIN-AWARE RAG PIPELINE)
# =========================
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"message": "Chat API endpoint is running (v4-rag-pipeline). Gunakan POST untuk mengirim pesan."})

    try:
        body = json.loads(request.body.decode("utf-8"))
        user_message = body.get("message", "").strip()
        if not user_message:
            return JsonResponse(
                {
                    "answer": "Pesan kosong.",
                    "reply": "Pesan kosong.",
                    "response": "Pesan kosong.",
                    "mode": "chatbot_public",
                    "intent": "unclear_gibberish",
                    "intent_confidence": 0.0,
                    "domain": "fallback_none",
                    "retrieval_confidence": 0.0,
                    "answerable": False,
                    "abstention_type": "unclear_question",
                    "sources": [],
                }
            )

        debug_raw = str(body.get("debug", "0")).strip().lower()
        include_debug = debug_raw in {"1", "true", "yes", "on"} or bool(getattr(settings, "DEBUG", False))
        requested_mode = str(body.get("mode", "chatbot_public")).strip().lower() or "chatbot_public"
        mode_aliases = {
            "chatbot": "chatbot_public",
            "public": "chatbot_public",
            "production": "chatbot_public",
            "evaluation": "evaluation_strict",
            "eval": "evaluation_strict",
            "strict": "evaluation_strict",
            "data": "internal_data",
        }
        response_mode = mode_aliases.get(requested_mode, requested_mode)
        if response_mode not in {"chatbot_public", "evaluation_strict", "internal_data"}:
            response_mode = "chatbot_public"

        normalized_question = _normalize_question(user_message)
        intent_result = route_intent(normalized_question)
        domain_result = route_domain(intent_result)

        if domain_result.get("retrieval_allowed"):
            try:
                top_k = int(body.get("top_k", 5) or 5)
            except (TypeError, ValueError):
                top_k = 5
            context_result = build_context_for_query(
                question=normalized_question,
                domain=str(domain_result.get("domain") or "fallback_none"),
                intent=str(intent_result.get("intent") or ""),
                mode=response_mode,
                top_k=top_k,
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
            question=normalized_question,
            intent=str(intent_result.get("intent") or ""),
            domain=str(domain_result.get("domain") or "fallback_none"),
            context_result=context_result,
            mode=response_mode,
        )
        generated = generate_response(
            question=normalized_question,
            intent_result=intent_result,
            domain_result=domain_result,
            context_result=context_result,
            grounding_result=grounding_result,
            mode=response_mode,
        )

        payload = {
            "answer": generated.get("answer", ""),
            "reply": generated.get("answer", ""),
            "response": generated.get("answer", ""),
            "mode": response_mode,
            "intent": intent_result.get("intent"),
            "intent_confidence": float(intent_result.get("confidence") or 0.0),
            "domain": domain_result.get("domain"),
            "retrieval_confidence": float(context_result.get("retrieval_confidence") or 0.0),
            "answerable": bool(generated.get("answerable")),
            "abstention_type": generated.get("abstention_type"),
            "sources": generated.get("sources", []),
        }
        if include_debug:
            payload["debug"] = {
                "question": normalized_question,
                "requested_mode": requested_mode,
                "intent": intent_result,
                "domain": domain_result,
                "context": {
                    "domain": context_result.get("domain"),
                    "retrieval_confidence": context_result.get("retrieval_confidence"),
                    "retrieval_summary": context_result.get("retrieval_summary"),
                    "error": context_result.get("error"),
                    "chunk_count": len(context_result.get("chunks") or []),
                },
                "grounding": {
                    "is_answerable": grounding_result.get("is_answerable"),
                    "confidence": grounding_result.get("confidence"),
                    "abstention_type": grounding_result.get("abstention_type"),
                    "reason": grounding_result.get("reason"),
                },
                "generation": generated.get("debug", {}),
            }
        return JsonResponse(payload)

    except Exception as e:
        return JsonResponse(
            {
                "answer": f"Server error: {e}",
                "reply": f"Server error: {e}",
                "response": f"Server error: {e}",
            },
            status=500,
        )
def _normalize_question(text: str) -> str:
    if text is None:
        return ""
    s = str(text).strip()
    if "Pertanyaan:" in s:
        s = s.split("Pertanyaan:")[-1].strip()
    prefix = "jawab dalam bahasa indonesia."
    s_low = s.lower()
    if s_low.startswith(prefix):
        s = s[len(prefix):].strip()
    return s.strip()
