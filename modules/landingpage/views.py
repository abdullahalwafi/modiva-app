import os
import re

from django.shortcuts import render, get_object_or_404, redirect
from modules.landingpage.models import ContactMessage
from .forms import *
from django.urls import reverse_lazy
from modules.vitamin.models import *
# Create your views here.

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

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME')
GROQ_URL = os.getenv('GROQ_URL')

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import requests

from modules.vector.models import DocumentChunk
from modules.vector.views import embed, get_chroma, get_model, rebuild_chroma_from_db

# =========================
# Helpers for RAG selection
# =========================
def _split_to_sentences(text: str):
    parts = []
    for chunk in text.replace("\r", "\n").split("\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        for seg in re.split(r"(?<=[.?!])\s+", chunk):
            s = seg.strip()
            if s:
                parts.append(s)
    return parts


def _best_sentence(doc_text: str, q_emb, q_text: str = ""):
    """Pick the most relevant sentence using cosine similarity."""
    sentences = _split_to_sentences(doc_text)
    if not sentences:
        return None, 0.0
    try:
        model = get_embedder()
        sent_embs = model.encode(sentences)
        import numpy as np

        sent_embs = np.array(sent_embs).astype("float32")
        qv = np.array(q_emb).astype("float32")
        sent_norms = np.linalg.norm(sent_embs, axis=1) + 1e-12
        q_norm = np.linalg.norm(qv) + 1e-12
        sims = (sent_embs @ qv) / (sent_norms * q_norm)
        idx = int(np.argmax(sims))
        return sentences[idx], float(sims[idx])
    except Exception:
        # Fallback: simple substring match
        lower_q = q_text.lower()
        for s in sentences:
            if lower_q in s.lower():
                return s, 1.0
        return sentences[0], 0.0


# cache the underlying model so we don't reload on every request
embedder = None


def get_embedder():
    global embedder
    if embedder is None:
        embedder = get_model()
    return embedder

# =========================
# CHROMA (persistent dari modules.vector)
# =========================
def get_collection():
    """
    Ambil koleksi Chroma shared dari modules.vector.
    Jika belum ada/masih kosong, coba rebuild dari DB.
    """
    client, collection = get_chroma()
    if client is None or collection is None:
        return None

    try:
        # Pastikan koleksi terisi (mis. setelah upload baru)
        if hasattr(collection, "count") and collection.count() == 0:
            rebuild_chroma_from_db()
            _, collection = get_chroma()
    except Exception:
        # Abaikan, tetap gunakan koleksi sekarang
        pass

    return collection

# =========================
# CHAT API
# =========================
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"message": "Chat API endpoint is running. Gunakan POST untuk mengirim pesan."}
        )

    try:
        body = json.loads(request.body.decode("utf-8"))
        user_message = body.get("message", "").strip()
        if not user_message:
            return JsonResponse({"reply": "Pesan kosong."})

        # 🔎 Chroma Vector Search + semantic fallback
        q_emb = embed(user_message)

        def query_chroma_with_rebuild():
            collection = get_collection()
            tried_rebuild = False
            while collection is not None:
                try:
                    results = collection.query(
                        query_embeddings=[q_emb],
                        n_results=5,
                        include=["documents", "metadatas", "ids"],
                    )
                except Exception as e:
                    print("Chroma query error:", e)
                    results = None

                docs = results.get("documents") if isinstance(results, dict) else None
                metas = results.get("metadatas") if isinstance(results, dict) else None
                ids = results.get("ids") if isinstance(results, dict) else None

                # normalize list-of-lists
                if isinstance(docs, list) and docs and isinstance(docs[0], list):
                    docs = docs[0]
                if isinstance(metas, list) and metas and isinstance(metas[0], list):
                    metas = metas[0]
                if isinstance(ids, list) and ids and isinstance(ids[0], list):
                    ids = ids[0]

                if docs:
                    normalized = []
                    for idx, doc in enumerate(docs):
                        text = " ".join([str(v) for v in doc.values()]) if isinstance(doc, dict) else str(doc)
                        meta = metas[idx] if metas and idx < len(metas) else {}
                        cid = ids[idx] if ids and idx < len(ids) else None
                        normalized.append({"text": text, "meta": meta, "id": cid})
                    return normalized

                if tried_rebuild:
                    break

                try:
                    rebuild_chroma_from_db()
                except Exception as rebuild_err:
                    print("Chroma rebuild gagal:", rebuild_err)
                    break

                collection = get_collection()
                tried_rebuild = True

            return []

        chroma_docs = query_chroma_with_rebuild()

        # gunakan kalimat terbaik dari tiap dokumen hasil vector search
        context_candidates = []
        for entry in chroma_docs:
            sent, score = _best_sentence(entry["text"], q_emb, user_message)
            if sent:
                context_candidates.append((score, sent))

        # fallback semantic search langsung ke DB jika belum dapat konteks
        if not context_candidates:
            for chunk in DocumentChunk.objects.all().order_by("-id"):
                text = str(chunk.content)
                sent, score = _best_sentence(text, q_emb, user_message)
                context_candidates.append((score, sent))

        # pilih 3 kalimat teratas
        context_candidates = sorted(
            [c for c in context_candidates if c[1]], key=lambda x: x[0], reverse=True
        )[:3]
        context_text = "\n\n".join([c[1] for c in context_candidates if c[1]])

        # ================================
        # Jika ada referensi → RAG
        # ================================
        if context_text.strip():
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Jawab hanya berdasarkan teks berikut. "
                            "Jangan menyebutkan dokumen atau sumber. "
                            "Gunakan HTML rapi."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Pertanyaan: {user_message}\n\nREFERENSI:\n{context_text}",
                    },
                ],
                "temperature": 0.1,
            }
        else:
            # Tanpa referensi → fallback
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": "Jawab langsung, gunakan HTML rapi."
                    },
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.5,
            }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        data = res.json()
        answer = data["choices"][0]["message"]["content"]

        return JsonResponse({"reply": answer})

    except Exception as e:
        return JsonResponse({"reply": f"Error: {e}"}, status=500)
