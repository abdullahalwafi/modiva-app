# modules/landingpage/views.py
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from modules.landingpage.models import ContactMessage
from .forms import ContactMessageForm
from modules.vitamin.models import Puskesmas, Sekolah

from .utils.chroma import get_collection
from .utils.context_builder import build_context_fullscan
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

        context_text, sources = build_context_fullscan(collection, user_message, max_chunks=8)
        if not context_text.strip():
            return JsonResponse({"reply": "Maaf, saya tidak tahu karena informasi tersebut tidak ada di dokumen."})
        res = ask_groq(user_message, context_text)

        if debug:
            return JsonResponse({
                "debug": True,
                "question": user_message,
                "context_length": len(context_text or ""),
                "context_preview": context_text[:1200] if context_text else "",
                "groq_status": res.status_code,
                "groq_text": res.text[:2000],
            })

        data = res.json()
        if "choices" not in data or not data["choices"]:
            return JsonResponse({"reply": f"Error dari Groq: {data}"}, status=500)

        answer = data["choices"][0]["message"]["content"]
        return JsonResponse({"reply": answer})

    except Exception as e:
        return JsonResponse({"reply": f"Server error: {e}"}, status=500)
