# modules/landingpage/views.py
import os
import re
import json
import requests

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from modules.landingpage.models import ContactMessage
from .forms import *
from django.urls import reverse_lazy
from modules.vitamin.models import *

# =========================
# PAGES (tetap)
# =========================
def homepage(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('landingpage:pendaftaran_sukses')
    else:
        form = ContactMessageForm()
    return render(request, 'index.html', {'form': form})

def about_us(request):
    return render(request, 'aboutUs.html')

def login(request):
    return render(request, 'login.html')

def lupa_password(request):
    return render(request, 'lupa_password.html')

def password_reset(request):
    return render(request, 'password_reset.html')

def mitra(request):
    try:
        puskesmas2 = Puskesmas.objects.all().order_by('id')[:4]
        sekolah2 = Sekolah.objects.all().order_by('id')[:4]
    except Exception as e:
        puskesmas2 = None
        sekolah2 = None
        print(f"Error occurred: {e}")
    return render(request, 'mitra.html', {'puskesmas2': puskesmas2, 'sekolah2': sekolah2})

def sk(request):
    return render(request, 'sk.html')

def privasi(request):
    return render(request, 'privasi.html')

def puskesmas(request):
    try:
        puskesmas = Puskesmas.objects.all().order_by('id')
    except Exception as e:
        puskesmas = None
        print(f"Error occurred: {e}")
    return render(request, 'puskesmas.html', {'puskesmas': puskesmas})

def sekolah(request):
    try:
        sekolah = Sekolah.objects.all().order_by('id')
    except Exception as e:
        sekolah = None
        print(f"Error occurred: {e}")
    return render(request, 'sekolah.html', {'sekolah': sekolah})

def profilpuskesmas(request, pk):
    puskesmas = get_object_or_404(Puskesmas, id=pk)
    return render(request, 'profil-puskesmas.html', {'puskesmas': puskesmas})

def profilsekolah(request, pk):
    sekolah = get_object_or_404(Sekolah, id=pk)
    return render(request, 'profil-sekolah.html', {'sekolah': sekolah})

def coba(request):
    return render(request, 'coba.html')

def daftar(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('landingpage:pendaftaran_sukses')
    else:
        form = ContactMessageForm()
    return render(request, 'daftar.html', {'form': form})

def pendaftaran_sukses(request):
    return render(request, 'pendaftaran_sukses.html')

# =========================
# GROQ CONFIG
# =========================
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME')
GROQ_URL = os.getenv('GROQ_URL')

# =========================
# CHROMA (shared dari modules.vector)
# =========================
from modules.vector.views import embed, get_chroma, get_model

def get_collection():
    """
    Ambil koleksi Chroma shared dari modules.vector.
    """
    client, collection = get_chroma()
    if client is None or collection is None:
        return None
    return collection

def _safe_get_all_chunks(collection, page_size: int = 500):
    """
    Ambil seluruh chunks dari Chroma (FULL SCAN).
    Return: (docs: list[str], metas: list[dict], ids: list[str])
    """
    docs_all, metas_all, ids_all = [], [], []

    # count() tidak selalu ada / bisa error, jadi optional
    try:
        total = collection.count()
    except Exception:
        total = None

    offset = 0
    try:
        while True:
            res = collection.get(
                include=["documents", "metadatas"],
                limit=page_size,
                offset=offset,
            )
            docs = res.get("documents", []) or []
            metas = res.get("metadatas", []) or []
            ids = res.get("ids", []) or []

            if not docs:
                break

            docs_all.extend([str(d) for d in docs])
            metas_all.extend(metas)
            ids_all.extend(ids)

            offset += len(docs)
            if total is not None and offset >= total:
                break

        return docs_all, metas_all, ids_all
    except Exception:
        # fallback: sekali get() tanpa paging
        res = collection.get(include=["documents", "metadatas"])
        docs_all = [str(d) for d in (res.get("documents", []) or [])]
        metas_all = res.get("metadatas", []) or []
        ids_all = res.get("ids", []) or []
        return docs_all, metas_all, ids_all

def _extract_keywords(user_message: str):
    """
    Ambil token penting untuk pencarian string (deterministik).
    - buang simbol
    - token >= 3 huruf
    - tambahkan juga frasa 2-4 kata (untuk nama)
    """
    cleaned = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ\s\-]", " ", user_message).strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    tokens = [t for t in parts if len(t) >= 3]

    phrases = []
    if len(parts) >= 2:
        for n in (4, 3, 2):
            if len(parts) >= n:
                phrases.append(" ".join(parts[:n]))
        # juga coba 2-3 kata terakhir (sering nama belakang)
        phrases.append(" ".join(parts[-2:]))
        if len(parts) >= 3:
            phrases.append(" ".join(parts[-3:]))

    out = []
    seen = set()
    for x in phrases + tokens:
        k = x.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(x)

    return out[:12]

def build_context_fullscan(collection, user_message: str, max_chunks: int = 10):
    """
    Konsep yang kamu minta:
    - "baca seluruh dokumen dulu" => ambil semua chunks dari Chroma (FULL SCAN)
    - pilih konteks relevan secara deterministik:
        1) keyword contains (nama/istilah)
        2) kalau tidak ketemu, fallback similarity embedding terhadap semua chunks
    """
    import numpy as np

    all_docs, all_metas, all_ids = _safe_get_all_chunks(collection)
    if not all_docs:
        return ""

    # =========================
    # 1) KEYWORD MATCH (deterministik)
    # =========================
    keywords = _extract_keywords(user_message)
    low_docs = [d.lower() for d in all_docs]

    hits = []
    for kw in keywords:
        kwl = kw.lower()
        for i, dlow in enumerate(low_docs):
            if kwl in dlow:
                hits.append(all_docs[i])

    if hits:
        # dedup dan ambil top max_chunks
        uniq = []
        seen = set()
        for h in hits:
            key = h[:200].lower()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(h)
            if len(uniq) >= max_chunks:
                break
        return "\n\n".join(uniq).strip()

    # =========================
    # 2) FALLBACK: embedding similarity vs semua chunks
    # =========================
    q_emb = np.array(embed(user_message), dtype=np.float32)

    model = get_model()
    embs = model.encode(all_docs, batch_size=64, show_progress_bar=False)
    embs = np.array(embs, dtype=np.float32)

    # cosine similarity
    doc_norm = np.linalg.norm(embs, axis=1) + 1e-12
    q_norm = np.linalg.norm(q_emb) + 1e-12
    sims = (embs @ q_emb) / (doc_norm * q_norm)

    top_idx = np.argsort(-sims)[:max_chunks]
    top_docs = [all_docs[int(i)] for i in top_idx if str(all_docs[int(i)]).strip()]
    return "\n\n".join(top_docs).strip()

# =========================
# CHAT API (FULL SCAN)
# =========================
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"message": "Chat API endpoint is running (v3-fullscan). Gunakan POST untuk mengirim pesan."}
        )

    try:
        body = json.loads(request.body.decode("utf-8"))
        user_message = body.get("message", "").strip()
        if not user_message:
            return JsonResponse({"reply": "Pesan kosong."})

        debug = str(body.get("debug", "0")) == "1"

        collection = get_collection()
        if collection is None:
            return JsonResponse({"reply": "Chroma belum siap / collection tidak tersedia."}, status=500)

        # ✅ FULL SCAN: baca semua chunks dulu, baru pilih konteks relevan
        context_text = build_context_fullscan(collection, user_message, max_chunks=10)

        # =========================
        # Build payload dulu (baru requests.post)
        # =========================
        if context_text.strip():
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Kamu adalah asisten ekstraksi informasi dari dokumen. "
                            "Jawab pertanyaan dengan mengambil informasi yang ada di REFERENSI. "
                            "Jika pertanyaan menanyakan 'siapa', jawab minimal: Nama, lokasi (jika ada), kontak (jika ada), ringkasan singkat. "
                            "Jika benar-benar tidak ada di referensi, jawab 'Tidak tahu'. "
                            'wajib kirim dengan bahasa indonesia dan full html'
                            "Jangan menyebutkan dokumen atau sumber. Gunakan HTML rapi."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Pertanyaan: {user_message}\n\n"
                            f"REFERENSI (gunakan untuk menjawab):\n{context_text}\n\n"
                            "Instruksi: Jawab berdasarkan referensi di atas."
                        ),
                    },
                ],
                "temperature": 0.1,
            }
        else:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Jika benar-benar tidak ada di referensi, jawab 'Tidak tahu'. "
                            'wajib kirim dengan bahasa indonesia dan full html'
                            "Jangan menyebutkan dokumen atau sumber. Gunakan HTML rapi."
                        )
                    },
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.5,
            }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        # Baru call Groq
        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)

        # ✅ DEBUG: lihat konteks + respon Groq mentah
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
