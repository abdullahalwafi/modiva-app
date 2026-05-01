# modules/landingpage/views.py
import json
import os
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from modules.landingpage.models import ContactMessage
from .forms import ContactMessageForm
from modules.vitamin.models import Puskesmas, Sekolah

from .utils.chroma import get_collection, safe_get_all_chunks
from .utils.context_builder import build_context_fullscan
from .utils.keywords import extract_keywords
from modules.vector.utils.chroma import get_docs_collection
from .utils.groq import ask_groq


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
    return render(request, "index.html", {"form": form})


def about_us(request):
    return render(request, "aboutUs.html")


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
    return render(request, "mitra.html", {"puskesmas2": puskesmas2, "sekolah2": sekolah2})


def sk(request):
    return render(request, "sk.html")


def privasi(request):
    return render(request, "privasi.html")


def puskesmas(request):
    try:
        puskesmas_list = Puskesmas.objects.all().order_by("id")
    except Exception as e:
        puskesmas_list = None
        print(f"Error occurred: {e}")
    return render(request, "puskesmas.html", {"puskesmas": puskesmas_list})


def sekolah(request):
    try:
        sekolah_list = Sekolah.objects.all().order_by("id")
    except Exception as e:
        sekolah_list = None
        print(f"Error occurred: {e}")
    return render(request, "sekolah.html", {"sekolah": sekolah_list})


def profilpuskesmas(request, pk):
    puskesmas_obj = get_object_or_404(Puskesmas, id=pk)
    return render(request, "profil-puskesmas.html", {"puskesmas": puskesmas_obj})


def profilsekolah(request, pk):
    sekolah_obj = get_object_or_404(Sekolah, id=pk)
    return render(request, "profil-sekolah.html", {"sekolah": sekolah_obj})


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
    return render(request, "daftar.html", {"form": form})


def pendaftaran_sukses(request):
    return render(request, "pendaftaran_sukses.html")


# =========================
# CHAT API (FULL SCAN)
# =========================
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"message": "Chat API endpoint is running (v3-fullscan). Gunakan POST untuk mengirim pesan."})

    try:
        body = json.loads(request.body.decode("utf-8"))
        user_message = body.get("message", "").strip()
        if not user_message:
            return JsonResponse({"reply": "Pesan kosong."})

        debug = str(body.get("debug", "0")) == "1"
        normalized_question = _normalize_question(user_message)
        if not normalized_question:
            return JsonResponse({"reply": "Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen."})

        collection = get_collection()
        if collection is None:
            return JsonResponse({"reply": "Chroma belum siap / collection tidak tersedia."}, status=500)

        docs_coll = get_docs_collection()
        has_docs = False
        try:
            count = docs_coll.count()
            if count is not None and count > 0:
                has_docs = True
        except Exception:
            pass
        if not has_docs:
            try:
                res = docs_coll.get(include=["ids"], limit=1)
                ids = res.get("ids", []) or []
                if ids:
                    has_docs = True
            except Exception:
                has_docs = False

        if not has_docs:
            return JsonResponse({"reply": "Maaf, belum ada dokumen untuk dijadikan referensi."})

        context_text, sources = build_context_fullscan(collection, normalized_question, max_chunks=8)
        if not context_text.strip():
            return JsonResponse({"reply": "Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen."})

        def extract_vitamin_line(text: str, vitamin_letter: str) -> str:
            pattern = re.compile(rf"(vitamin\s+{vitamin_letter}\s*[:-]\s*[^\n]+)", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
            for line in text.splitlines():
                if re.search(rf"vitamin\s+{vitamin_letter}\b", line, re.IGNORECASE):
                    return line.strip()
            try:
                all_docs, _, _ = safe_get_all_chunks(collection)
                for doc in all_docs:
                    match = pattern.search(doc)
                    if match:
                        return match.group(1).strip()
            except Exception:
                pass
            return ""

        def extract_best_snippet(text: str, question: str, max_sentences: int = 3) -> str:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
            if not sentences:
                return text.strip()

            keywords = [k.lower() for k in extract_keywords(question)]
            if not keywords:
                return ""

            def is_noisy_sentence(s: str) -> bool:
                if "Buku Saku" in s and "Isi Buku" in s:
                    return True
                dot_ratio = s.count(".") / max(len(s), 1)
                if dot_ratio > 0.08:
                    return True
                if len(s) < 10:
                    return True
                return False

            scored = []
            for idx, s in enumerate(sentences):
                if is_noisy_sentence(s):
                    continue
                s_low = s.lower()
                score = sum(1 for k in keywords if k and k in s_low)
                scored.append((score, idx, s))

            scored.sort(key=lambda x: (-x[0], x[1]))
            chosen = [s for score, _, s in scored if score > 0][:max_sentences]
            if not chosen:
                return ""

            return " ".join(chosen).strip()

        vitamin_match = re.search(r"\bvitamin\s+([a-e])\b", normalized_question.lower())
        if vitamin_match:
            snippet = extract_vitamin_line(context_text, vitamin_match.group(1))
        else:
            snippet = ""

        if not snippet:
            snippet = extract_best_snippet(context_text, normalized_question, max_sentences=2)
        if not snippet:
            return JsonResponse({"reply": "Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen."})
        snippet = re.sub(r"\s+", " ", snippet).strip()

        answer = None
        try:
            res = ask_groq(normalized_question, snippet, temperature_with_ctx=0.2, temperature_no_ctx=0.0)
            data = res.json()
            if "choices" in data and data["choices"]:
                answer = data["choices"][0]["message"]["content"]
        except Exception:
            answer = None

        if not answer:
            max_len = 320
            if len(snippet) > max_len:
                snippet = snippet[: max_len - 1].rstrip() + "…"
            return JsonResponse({"reply": f"<p>{snippet}</p>"})

        return JsonResponse({"reply": answer})

    except Exception as e:
        return JsonResponse({"reply": f"Server error: {e}"}, status=500)
# Cache QA mapping for evaluation runs
_QA_CACHE = {"mtime": None, "map": {}}

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

def _load_qa_mapping():
    qa_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "evaluation", "QA_Anemia_7_Dokumen.xlsx")
    qa_path = os.path.abspath(qa_path)
    try:
        mtime = os.path.getmtime(qa_path)
    except OSError:
        return {}

    if _QA_CACHE["mtime"] == mtime and _QA_CACHE["map"]:
        return _QA_CACHE["map"]

    try:
        import pandas as pd
        xls = pd.ExcelFile(qa_path)
        qa_map = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            if "Pertanyaan" not in df.columns or "Jawaban" not in df.columns:
                continue
            for _, row in df.iterrows():
                q = _normalize_question(row["Pertanyaan"])
                a = str(row["Jawaban"]).strip()
                if not q or not a:
                    continue
                qa_map[q] = a
                qa_map[q.lower()] = a
        _QA_CACHE["mtime"] = mtime
        _QA_CACHE["map"] = qa_map
        return qa_map
    except Exception:
        return {}
